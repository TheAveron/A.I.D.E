from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import create_access_token, hash_password
from ..crud import authenticate_user, create_user, get_user_by_username
from ..database import get_db
from ..schemas import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account and return a JWT token with user info.
    """
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    hashed_password = hash_password(user.password)

    db_user = create_user(
        db=db,
        username=user.username,
        hashed_password=hashed_password,
        admin=user.is_admin,
    )

    # Create JWT token for immediate login
    token = create_access_token(data={"sub": db_user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user.user_id,
        "username": db_user.username,
    }


@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": authenticated_user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": authenticated_user.user_id,
        "username": authenticated_user.username,
    }
