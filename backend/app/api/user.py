from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import user as crud_user
from ..database import get_db
from ..schemas import UserFull

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserFull, status_code=status.HTTP_200_OK)
def read_current_user(current_user=Depends(get_current_user)):
    return current_user


@router.get("/faction/{faction_id}", response_model=list[UserFull])
def get_users_by_faction(faction_id: int, db: Session = Depends(get_db)):
    users = crud_user.get_users_by_faction(db, faction_id)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error getting user list for faction: {faction_id}",
        )
    return users


@router.get(
    "/from_name/{username}", response_model=UserFull, status_code=status.HTTP_200_OK
)
def read_user_by_name(username: str, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get(
    "/detail/{user_id}", response_model=UserFull, status_code=status.HTTP_200_OK
)
def read_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
