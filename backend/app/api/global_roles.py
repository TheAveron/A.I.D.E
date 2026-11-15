"""Server-wide roles (admin, train admin...): only an admin hands them out."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..core import require_global_role
from ..database import GlobalRole, GlobalRoleName, User, get_db
from ..schemas import GlobalRoleOut

router = APIRouter(prefix="/global-roles", tags=["Global roles"])

_admin_only = require_global_role(GlobalRoleName.ADMIN.value)


def _out(grant: GlobalRole, username: str) -> GlobalRoleOut:
    return GlobalRoleOut(
        user_id=grant.user_id,
        username=username,
        role=grant.role,
        granted_at=grant.granted_at,
    )


def _user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("", response_model=list[GlobalRoleOut])
def list_global_roles(db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    """Everybody who holds a server-wide role."""
    rows = (
        db.query(GlobalRole, User.username)
        .join(User, User.user_id == GlobalRole.user_id)
        .order_by(User.username, GlobalRole.role)
        .all()
    )
    return [_out(grant, username) for grant, username in rows]


@router.put("/{user_id}/{role}", response_model=GlobalRoleOut)
def grant_global_role(
    user_id: int,
    role: GlobalRoleName,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Give `role` to a user (nothing changes if they already have it)."""
    user = _user_or_404(db, user_id)
    user.add_global_role(role.value)
    db.commit()
    db.refresh(user)
    grant = next(r for r in user.global_roles if r.role == role.value)
    return _out(grant, user.username)


@router.delete("/{user_id}/{role}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_global_role(
    user_id: int,
    role: GlobalRoleName,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    user = _user_or_404(db, user_id)
    if role is GlobalRoleName.ADMIN and user.has_global_role(role.value):
        admins = db.query(GlobalRole).filter(GlobalRole.role == role.value).count()
        if admins <= 1:
            # Without an admin nobody could ever hand the role out again.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You cannot remove the last admin",
            )
    user.remove_global_role(role.value)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
