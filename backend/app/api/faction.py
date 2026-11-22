import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import audit
from ..crud import faction as faction_crud
from ..crud import faction_role as faction_role_crud
from ..crud import normalize
from ..crud.notification import notify
from ..database import User, get_db
from ..misc import (DEPUTY_ROLE_NAME, LEADER_ROLE_NAME, FactionPermission,
                    check_faction_permission)
from ..schemas import (FactionCreate, FactionOut, FactionUpdate,
                       LeadershipTransfer)
from .documentation import archive_faction_folder, move_faction_folder

logger = logging.getLogger("aide")

NO_FACTION_NAME = "Sans Faction"

router = APIRouter(
    prefix="/factions",
    tags=["Factions"],
)


def _check_name_usable(
    db: Session, name: str, exclude_faction_id: int | None = None
) -> None:
    """Reject names that can't get their own documents folder."""
    if not normalize(name):
        raise HTTPException(
            status_code=400, detail="Faction name must contain at least one letter"
        )
    if faction_crud.normalized_name_taken(db, name, exclude_faction_id):
        raise HTTPException(
            status_code=409, detail="A faction with a similar name already exists"
        )


def _is_leader_of(user: User, faction) -> bool:
    """Being "Chef" of another faction gives no right on this one."""
    role = user.role
    return (
        user.faction_id == faction.faction_id
        and role is not None
        and role.faction_id == faction.faction_id
        and role.name == LEADER_ROLE_NAME
    )


@router.post("/create", response_model=FactionOut, status_code=status.HTTP_201_CREATED)
def create_faction(
    faction_data: FactionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FactionOut:
    """
    Create a new faction.

    Parameters:
    - faction: Faction data including name

    Returns:
    - FactionOut: Created faction data

    Raises:
    - 409: Faction already exists
    - 422: Invalid faction data
    """
    user_faction = (
        faction_crud.get_faction_by_user_id(db, user.user_id) if user else None
    )

    if user_faction and user_faction.name != "Sans Faction":
        raise HTTPException(status_code=400, detail="User already belongs to a faction")

    if faction_crud.get_faction_by_name(db, faction_data.name):
        raise HTTPException(status_code=409, detail="Faction name already exists")

    _check_name_usable(db, faction_data.name)

    return faction_crud.create_faction(db, faction_data, user.user_id)


@router.get("/list", response_model=list[FactionOut], status_code=status.HTTP_200_OK)
def list_factions(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    db: Session = Depends(get_db),
):
    return faction_crud.list_factions(db, skip=skip, limit=limit)


@router.get("/member_counts", response_model=dict[int, int])
def member_counts(db: Session = Depends(get_db)) -> dict[int, int]:
    """Members per faction, in one query (the list page used one request each)."""
    return faction_crud.count_members(db)


@router.get(
    "/detail/{faction_id}", response_model=FactionOut, status_code=status.HTTP_200_OK
)
def get_faction(faction_id: int, db: Session = Depends(get_db)):
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    return faction


@router.put(
    "/update/{faction_id}",
    response_model=FactionOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def update_faction(
    faction_id: int,
    faction_update: FactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    # Which fields the client actually sent (as opposed to left unset) -
    # mirrors the exclude_unset=True logic used in update_faction_validation.
    provided_fields = faction_update.model_dump(exclude_unset=True)

    # is_approved is the server's own "this faction is legitimate" stamp:
    # it must only ever be set by a real admin, never by a faction's own
    # leadership (manage_roles is a faction-internal permission, not a
    # staff one).
    if "is_approved" in provided_fields and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a server admin can approve or unapprove a faction",
        )

    # Any other field (name, description, ...) still goes through the
    # normal faction-scoped permission check.
    other_fields = {k: v for k, v in provided_fields.items() if k != "is_approved"}
    if other_fields:
        check_faction_permission(
            current_user,
            FactionPermission.MANAGE_ROLES,
            target_faction_id=faction.faction_id,
        )

    new_name = provided_fields.get("name")
    if new_name is not None and new_name != faction.name:
        _check_name_usable(db, new_name, exclude_faction_id=faction.faction_id)

    old_name = faction.name
    approval_before = bool(faction.is_approved)
    # The documents folder is named after the faction: it moves with it, and goes back if the database refuses the rename.
    moved = (
        new_name is not None
        and new_name != old_name
        and move_faction_folder(old_name, new_name)
    )
    try:
        updated_faction = faction_crud.update_faction_validation(
            db, faction, faction_update
        )
    except Exception as e:
        if moved:
            move_faction_folder(new_name, old_name)
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        raise
    if bool(updated_faction.is_approved) != approval_before:
        audit.record(
            db,
            current_user,
            (
                audit.AuditAction.FACTION_APPROVED
                if updated_faction.is_approved
                else audit.AuditAction.FACTION_UNAPPROVED
            ),
            "faction",
            updated_faction.faction_id,
            updated_faction.name,
        )
        db.commit()
    return updated_faction


@router.post("/transfer/{faction_id}", response_model=FactionOut)
def transfer_leadership(
    faction_id: int,
    body: LeadershipTransfer,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The leader hands the faction over to another of its members.

    The new leader gets the "Chef" role; the former one becomes "Chef Adjoint"
    (or, if the faction has no such role any more, its most powerful other
    role), so the faction always has exactly one leader.
    """
    faction = faction_crud.get_faction(db, faction_id)
    if not faction or faction.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Faction not found")

    if not _is_leader_of(current_user, faction):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the faction's leader can hand it over",
        )

    if body.user_id == current_user.user_id:
        raise HTTPException(
            status_code=400, detail="You already are the faction's leader"
        )
    successor = db.query(User).filter(User.user_id == body.user_id).first()
    if not successor or successor.faction_id != faction.faction_id:
        raise HTTPException(
            status_code=404, detail="This user is not a member of the faction"
        )

    roles = faction_role_crud.get_roles_by_faction(db, faction.faction_id)
    leader_role = next((r for r in roles if r.name == LEADER_ROLE_NAME), None)
    if leader_role is None:
        raise HTTPException(status_code=409, detail="The faction has no leader role")

    def power(role) -> int:
        return sum(role.has_permission(p.value) for p in FactionPermission)

    others = [r for r in roles if r.name != LEADER_ROLE_NAME]
    former_role = next((r for r in others if r.name == DEPUTY_ROLE_NAME), None) or (
        max(others, key=power, default=None)
    )
    if former_role is None:
        raise HTTPException(
            status_code=409,
            detail="Create a role for the former leader first",
        )

    successor.role_id = leader_role.role_id
    current_user.role_id = former_role.role_id
    notify(
        db,
        successor.user_id,
        "leadership",
        f"{current_user.username} vous a nommé chef de {faction.name}",
        f"/faction/{faction.faction_id}",
    )
    db.commit()
    db.refresh(faction)
    return faction


@router.delete("/delete/{faction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faction(
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a faction: its leader (or an admin) archives it.

    Members go back to "Sans Faction", open offers are cancelled, the faction
    leaves every listing and its name is freed. Its documents are kept in an
    archive folder and its past trades stay readable.
    """
    faction = faction_crud.get_faction(db, faction_id)
    if not faction or faction.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Faction not found")

    if faction.name == NO_FACTION_NAME:
        raise HTTPException(status_code=400, detail="This faction can't be deleted")

    if not (_is_leader_of(current_user, faction) or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the faction's leader can delete it",
        )

    old_name = faction.name
    # asked now: archiving sends the leader back to "Sans Faction"
    acts_as_leader = _is_leader_of(current_user, faction)
    moved = None
    try:
        faction_crud.archive_faction(db, faction, current_user)
        moved = archive_faction_folder(old_name, faction.faction_id)
        if not acts_as_leader:
            # an admin acting on somebody else's faction leaves a trace
            audit.record(
                db,
                current_user,
                audit.AuditAction.FACTION_DELETED,
                "faction",
                faction.faction_id,
                old_name,
            )
        db.commit()
    except Exception:
        db.rollback()
        if moved:
            source, target = moved
            try:
                target.rename(source)
            except OSError:
                logger.exception("Could not restore documents %s", source)
        raise
    return None
