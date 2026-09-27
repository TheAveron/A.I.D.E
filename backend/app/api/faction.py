from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import faction as faction_crud
from ..database import User, get_db
from ..misc import FactionPermission, check_faction_permission
from ..schemas import FactionCreate, FactionOut, FactionUpdate

router = APIRouter(
    prefix="/factions",
    tags=["Factions"],
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
    - 400: Faction already exists
    - 422: Invalid faction data
    """
    user_faction = (
        faction_crud.get_faction_by_user_id(db, user.user_id) if user else None
    )

    if user_faction and user_faction.name != "Sans Faction":
        raise HTTPException(status_code=400, detail="User already belongs to a faction")

    if faction_crud.get_faction_by_name(db, faction_data.name):
        raise HTTPException(status_code=400, detail="Faction name already exists")

    return faction_crud.create_faction(db, faction_data, user.user_id)


@router.get("/list", response_model=list[FactionOut], status_code=status.HTTP_200_OK)
def list_factions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return faction_crud.list_factions(db, skip=skip, limit=limit)


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
    provided_fields = faction_update.dict(exclude_unset=True)

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

    try:
        updated_faction = faction_crud.update_faction_validation(
            db, faction, faction_update
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated_faction


@router.delete("/delete/{faction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faction(
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    check_faction_permission(
        current_user, FactionPermission.MANAGE_ROLES, target_faction_id=faction.faction_id
    )

    faction_crud.delete_faction(db, faction)
    return None
