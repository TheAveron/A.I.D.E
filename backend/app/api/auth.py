from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core import create_user_token, get_current_user, hash_password
from ..core.ratelimit import LoginLimiter
from ..core.security import verify_password
from ..crud import (
    authenticate_user,
    create_user,
    get_faction_by_name,
    get_roles_by_faction,
    username_taken,
)
from ..database import User, get_db
from ..schemas import Auth, PasswordChange, UserCreate, UserLogin

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
    name_in_use = HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
    )
    if username_taken(db, user.username):
        raise name_in_use

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
        raise name_in_use

    token = create_user_token(user_register)

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
    token = create_user_token(user_login)

    return Auth(
        access_token=token,
        token_type="bearer",
        user_id=user_login.user_id,
        username=user_login.username,
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Auth:
    """Change the logged-in user's password; the answer holds a fresh token.

    The current password is asked again, so that a stolen session alone can't
    take the account over, and wrong guesses are limited like login attempts.
    """
    key = f"password|{current_user.user_id}"
    wait = login_limiter.retry_after(key)
    if wait:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts, try again later",
            headers={"Retry-After": str(wait)},
        )

    if not verify_password(body.current_password, current_user.hashed_password):
        login_limiter.record_failure(key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current password is incorrect",
        )
    login_limiter.reset(key)

    if body.new_password == body.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new password must differ from the current one",
        )

    current_user.hashed_password = hash_password(body.new_password)
    # Every other session of this account is signed out
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()

    token = create_user_token(current_user)
    return Auth(
        access_token=token,
        token_type="bearer",
        user_id=current_user.user_id,
        username=current_user.username,
    )
