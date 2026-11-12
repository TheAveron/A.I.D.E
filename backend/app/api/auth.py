from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core import create_access_token, hash_password
from ..core.ratelimit import LoginLimiter
from ..crud import (authenticate_user, create_user, get_faction_by_name,
                    get_roles_by_faction, get_user_by_username)
from ..database import get_db
from ..schemas import Auth, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["Auth"])

# 10 failed attempts per client address and username every 5 minutes.
login_limiter = LoginLimiter(max_failures=10, window=300)


def _login_key(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}|{username.casefold()}"


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)) -> Auth:
    """
    Register a new user account and return a JWT token with user info.
    """
    username_taken = HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
    )
    if get_user_by_username(db, user.username):
        raise username_taken

    hashed_password = hash_password(user.password)

    faction = get_faction_by_name(db, "Sans Faction")

    faction_id = None
    role_id = None

    if faction:
        faction_id = faction.faction_id

        roles = get_roles_by_faction(db, faction.faction_id)

        for role in roles:
            if role.name == "Membre":
                role_id = role.role_id
                break

    try:
        user_register = create_user(
            db=db,
            username=user.username,
            hashed_password=hashed_password,
            admin=False,
            faction_id=faction_id,
            role_id=role_id,
        )
    except IntegrityError:
        # Two registrations for the same name raced past the check above.
        db.rollback()
        raise username_taken

    token = create_access_token(data={"sub": user.username})

    return Auth(
        access_token=token,
        token_type="bearer",
        user_id=user_register.user_id,
        username=user_register.username,
    )


@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login(user: UserLogin, request: Request, db: Session = Depends(get_db)) -> Auth:
    key = _login_key(request, user.username)

    # Checked before the password, so that a locked key can't be used to keep
    # guessing: even the right password is refused until the lock expires.
    wait = login_limiter.retry_after(key)
    if wait:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts, try again later",
            headers={"Retry-After": str(wait)},
        )

    user_login = authenticate_user(db, user.username, user.password)
    if not user_login:
        login_limiter.record_failure(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    login_limiter.reset(key)
    token = create_access_token(data={"sub": user_login.username})

    return Auth(
        access_token=token,
        token_type="bearer",
        user_id=user_login.user_id,
        username=user_login.username,
    )
