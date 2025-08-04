from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.crud.faction import get_faction_by_user_id

from ..core import get_current_user
from ..crud import faction_role as crud_role
from ..database import User, get_db
from ..schemas import RoleCreate, RoleOut, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


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
    current_user: User = Depends(get_current_user),
):
    if not (current_user.role and current_user.role.manage_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to create faction role",
        )

    return crud_role.create_role(db, faction_id, role_in)


@router.get("/faction/{faction_id}", response_model=list[RoleOut])
def get_roles_by_faction(faction_id: int, db: Session = Depends(get_db)):
    return crud_role.get_roles_by_faction(db, faction_id)


@router.get("/detail/{role_id}", response_model=RoleOut)
def get_role_by_id(role_id: int, db: Session = Depends(get_db)):
    role = crud_role.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


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

    if not (current_user.role and current_user.role.manage_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to update faction roles",
        )

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

    if not (current_user.role and current_user.role.manage_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to delete faction role",
        )

    crud_role.delete_role(db, role)
