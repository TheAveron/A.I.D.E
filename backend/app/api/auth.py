from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import create_access_token, hash_password
from ..crud import (authenticate_user, create_user, get_faction_by_name,
                    get_roles_by_faction, get_user_by_username)
from ..database import get_db
from ..schemas import Auth, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)) -> Auth:
    """
    Register a new user account and return a JWT token with user info.
    """
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    hashed_password = hash_password(user.password)

    faction = get_faction_by_name(db, "Sans Faction")

    faction_id = None
    role_id = None

    if faction:
        faction_id = faction.faction_id

        roles = get_roles_by_faction(db, faction.faction_id)

        for role in roles:
            if role.name == "Membre":
                role_id = role.id
                break

    user_register = create_user(
        db=db,
        username=user.username,
        hashed_password=hashed_password,
        admin=user.is_admin,
        faction_id=faction_id,
        role_id=role_id,
    )

    token = create_access_token(data={"sub": user.username})

    return Auth(
        access_token=token,
        token_type="bearer",
        user_id=user_register.user_id,
        username=user_register.username,
    )


@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login(user: UserLogin, db: Session = Depends(get_db)) -> Auth:
    user_login = authenticate_user(db, user.username, user.password)
    if not user_login:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user_login.username})

    return Auth(
        access_token=token,
        token_type="bearer",
        user_id=user_login.user_id,
        username=user_login.username,
    )
