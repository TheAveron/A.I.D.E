from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import faction_role as crud_role
from ..database import Role, User, get_db
from ..misc import (FactionPermission, check_faction_permission,
                    require_faction_permission)
from ..schemas import RoleCreate, RoleOut, RoleUpdate

LEADER_ROLE_NAME = "Chef"
GUEST_ROLE_NAME = "Invité"

router = APIRouter(prefix="/roles", tags=["Roles"])


def _forbid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _check_can_grant(actor: User, wanted: dict[str, bool]) -> None:
    """Nobody hands out - or takes away - powers they don't hold themselves.

    `wanted` maps permission names to the value the role would get. This is
    what stops a member with `manage_roles` from turning their own (or any)
    role into something more powerful than what they have.
    """
    actor_role = actor.role
    for permission in FactionPermission:
        if permission.value in wanted and not actor_role.has_permission(
            permission.value
        ):
            raise _forbid(
                "You can't change a permission you don't have yourself "
                f"({permission.value})"
            )


@router.get("/faction/{faction_id}", response_model=list[RoleOut])
def list_faction_roles(faction_id: int, db: Session = Depends(get_db)):
    roles = crud_role.get_roles_by_faction(db, faction_id)
    if not roles:
        raise HTTPException(status_code=404, detail="No roles found for this faction")
    return roles


@router.post(
    "/faction/{faction_id}/create",
    response_model=RoleOut,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    faction_id: int,
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_faction_permission(FactionPermission.MANAGE_ROLES)
    ),
):
    if role_in.name in (LEADER_ROLE_NAME, GUEST_ROLE_NAME):
        raise _forbid(f"The '{role_in.name}' role is created with the faction")

    granted = {
        p.value: True for p in FactionPermission if getattr(role_in, p.value, False)
    }
    _check_can_grant(current_user, granted)

    return crud_role.create_role(db, faction_id, role_in)


@router.get("/detail/{role_id}", response_model=RoleOut)
def get_role_by_id(role_id: int, db: Session = Depends(get_db)):
    role = crud_role.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


def _check_can_edit(current_user: User, role: Role) -> None:
    check_faction_permission(
        current_user, FactionPermission.MANAGE_ROLES, target_faction_id=role.faction_id
    )
    if role.name == LEADER_ROLE_NAME:
        raise _forbid("The leader role can't be modified or deleted")
    if role.role_id == current_user.role_id:
        raise _forbid("You can't modify or delete your own role")


@router.put("/update/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = crud_role.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # The target faction can only be known once the role has been
    # fetched (a role_id alone doesn't reveal its faction), so this
    # can't use the require_faction_permission(...) dependency and is
    # checked explicitly instead.
    _check_can_edit(current_user, role)

    changes = role_update.model_dump(exclude_unset=True)

    new_name = changes.get("name")
    if new_name is not None and new_name != role.name:
        # The guest role is what joining a faction relies on.
        if role.name == GUEST_ROLE_NAME:
            raise _forbid(f"The '{GUEST_ROLE_NAME}' role can't be renamed")
        if new_name in (LEADER_ROLE_NAME, GUEST_ROLE_NAME):
            raise _forbid(f"The name '{new_name}' is reserved")

    changed_permissions = {
        p.value: changes[p.value]
        for p in FactionPermission
        if p.value in changes and changes[p.value] != getattr(role, p.value)
    }
    _check_can_grant(current_user, changed_permissions)

    return crud_role.update_role(db, role, role_update)


@router.delete("/delete/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = crud_role.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    _check_can_edit(current_user, role)
    if role.name == GUEST_ROLE_NAME:
        raise _forbid(f"The '{GUEST_ROLE_NAME}' role can't be deleted")

    crud_role.delete_role(db, role)
