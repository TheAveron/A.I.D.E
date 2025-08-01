from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import hash_password, create_access_token
from ..crud import authenticate_user, create_user, get_user_by_username
from ..database import get_db
from ..schemas import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(user.password)
    db_user = create_user(
        db=db,
        username=user.username,
        hashed_password=hashed,
        faction_id=None,
        role_id=None,
        admin=user.is_admin,
    )
    return db_user


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": authenticated_user.username})
    return {"access_token": token, "token_type": "bearer"}
