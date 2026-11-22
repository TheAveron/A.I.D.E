"""The administration panel's API.

Everything here is for admins, except the audit trail, which train admins may
read for what concerns trains, lines and stations, and money admins for what
concerns currencies.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ..core import hash_password, require_global_role
from ..crud import audit
from ..crud import faction as faction_crud
from ..crud.notification import notify
from ..database import AuditLog, Faction, GlobalRoleName, Role, User, get_db
from ..schemas import (AdminFactionOut, AdminPasswordReset, AdminUserOut,
                       AuditLogOut)
from .user import LEADER_ROLE_NAME, _in_a_real_faction, _send_to_no_faction

router = APIRouter(prefix="/admin", tags=["Administration"])

ADMIN = GlobalRoleName.ADMIN.value
TRAIN_ADMIN = GlobalRoleName.TRAIN_ADMIN.value
MONEY_ADMIN = GlobalRoleName.MONEY_ADMIN.value

_admin_only = require_global_role(ADMIN)
_staff = require_global_role(ADMIN, TRAIN_ADMIN, MONEY_ADMIN)


def _escape_like(text: str) -> str:
    return text.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/audit", response_model=list[AuditLogOut])
def read_audit(
    action: Optional[str] = Query(None, max_length=40),
    target_type: Optional[str] = Query(None, max_length=20),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Session = Depends(get_db),
    staff: User = Depends(_staff),
):
    """The staff trail, newest first. A train admin only sees train matters,
    a money admin currency matters (both, for somebody holding both roles)."""
    query = db.query(AuditLog)
    if not staff.has_global_role(ADMIN):
        targets: list[str] = []
        if staff.has_global_role(TRAIN_ADMIN):
            targets += audit.TRAIN_TARGETS
        if staff.has_global_role(MONEY_ADMIN):
            targets += audit.MONEY_TARGETS
        query = query.filter(AuditLog.target_type.in_(targets))
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    return query.order_by(AuditLog.log_id.desc()).offset(skip).limit(limit).all()


def _user_out(user: User, faction_names: dict, role_names: dict) -> AdminUserOut:
    return AdminUserOut(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        faction_id=user.faction_id,
        faction_name=faction_names.get(user.faction_id),
        role_id=user.role_id,
        role_name=role_names.get(user.role_id),
        global_roles=user.global_role_names,
        created_at=user.created_at,
    )


@router.get("/users", response_model=list[AdminUserOut])
def search_users(
    q: Optional[str] = Query(None, max_length=60, description="Name or email"),
    role: Optional[str] = Query(None, max_length=30, description="A global role"),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Accounts, by name or email, with their faction and global roles."""
    from ..database import GlobalRole

    query = db.query(User)
    if q and q.strip():
        pattern = f"%{_escape_like(q)}%"
        query = query.filter(
            User.username.ilike(pattern, escape="\\")
            | User.email.ilike(pattern, escape="\\")
        )
    if role:
        query = query.filter(
            User.user_id.in_(
                db.query(GlobalRole.user_id).filter(GlobalRole.role == role)
            )
        )
    users = query.order_by(User.username).offset(skip).limit(limit).all()

    faction_names = {
        fid: name
        for fid, name in db.query(Faction.faction_id, Faction.name).filter(
            Faction.faction_id.in_({u.faction_id for u in users if u.faction_id})
        )
    }
    role_names = {
        rid: name
        for rid, name in db.query(Role.role_id, Role.name).filter(
            Role.role_id.in_({u.role_id for u in users if u.role_id})
        )
    }
    return [_user_out(u, faction_names, role_names) for u in users]


def _target_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: int,
    body: AdminPasswordReset,
    db: Session = Depends(get_db),
    admin: User = Depends(_admin_only),
):
    """Give an account a new password (the owner is told to change it)."""
    user = _target_user(db, user_id)
    user.hashed_password = hash_password(body.new_password)
    user.token_version = (user.token_version or 0) + 1  # signs them out
    audit.record(
        db, admin, audit.AuditAction.PASSWORD_RESET, "user", user.user_id, user.username
    )
    notify(
        db,
        user.user_id,
        "password_reset",
        "Un administrateur a réinitialisé votre mot de passe : changez-le dès "
        "votre connexion.",
        "/profile",
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users/{user_id}/detach", response_model=AdminUserOut)
def remove_from_faction(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(_admin_only),
):
    """Send somebody back to "Sans Faction". A leader must hand over first."""
    user = _target_user(db, user_id)
    if not _in_a_real_faction(user):
        raise HTTPException(
            status_code=400, detail="This user doesn't belong to a faction"
        )
    if user.role and user.role.name == LEADER_ROLE_NAME:
        raise HTTPException(
            status_code=409,
            detail="A faction leader must hand the leadership over first",
        )
    old_faction = user.faction.name
    _send_to_no_faction(db, user)
    audit.record(
        db,
        admin,
        audit.AuditAction.USER_REMOVED_FROM_FACTION,
        "user",
        user.user_id,
        user.username,
        f"Retiré de {old_faction}",
    )
    notify(
        db,
        user.user_id,
        "kicked",
        f"Un administrateur vous a retiré de la faction {old_faction}.",
    )
    db.commit()
    db.refresh(user)
    faction_names = {user.faction_id: user.faction.name if user.faction else None}
    role_names = {user.role_id: user.role.name if user.role else None}
    return _user_out(user, faction_names, role_names)


@router.get("/factions", response_model=list[AdminFactionOut])
def list_all_factions(
    state: str = Query("all", pattern="^(all|pending|approved|archived)$"),
    q: Optional[str] = Query(None, max_length=100),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Every faction, archived ones included, to approve or review them."""
    query = db.query(Faction)
    if state == "archived":
        query = query.filter(Faction.deleted_at.isnot(None))
    else:
        query = query.filter(Faction.deleted_at.is_(None))
        if state == "pending":
            query = query.filter(Faction.is_approved.is_(False))
        elif state == "approved":
            query = query.filter(Faction.is_approved.is_(True))
    if q and q.strip():
        query = query.filter(Faction.name.ilike(f"%{_escape_like(q)}%", escape="\\"))
    factions = query.order_by(Faction.name).offset(skip).limit(limit).all()
    counts = faction_crud.count_members(db)
    return [
        AdminFactionOut(
            faction_id=f.faction_id,
            name=f.name,
            is_approved=bool(f.is_approved),
            requires_approval=f.requires_approval,
            member_count=counts.get(f.faction_id, 0),
            created_at=f.created_at,
            deleted_at=f.deleted_at,
        )
        for f in factions
    ]
