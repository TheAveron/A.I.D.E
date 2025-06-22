from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core import get_current_user
from crud import get_user_by_username
from database import get_db
from schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_current_user(current_user=Depends(get_current_user)):
    return current_user


@router.get("/{username}", response_model=UserOut)
def read_user(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
