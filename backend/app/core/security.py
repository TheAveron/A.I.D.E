import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import User, get_db
from .settings import SECRET_KEY

# Same logger as main.py: it is configured there, so don't add handlers again
logger = logging.getLogger("aide")


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)  # tokenUrl must match your login route


# Same login route, but a missing token is not an error (see get_optional_user).
oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed)
    except ValueError:
        # bcrypt refuses passwords over 72 bytes: no such password can match.
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    if SECRET_KEY is None:
        raise ValueError("No SECRET_KEY environment variable set")

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_user_token(user: User) -> str:
    """A token for `user`, valid until their password next changes."""
    return create_access_token(
        data={"sub": user.username, "tv": user.token_version or 0}
    )


def get_current_user(token=Depends(oauth2_scheme), db: Session = Depends(get_db)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:

        if SECRET_KEY is None:
            raise ValueError("No SECRET_KEY environment variable set")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.debug("JWT valid but missing 'sub' claim")
            raise credentials_exception

    except jwt.PyJWTError:
        logger.debug("JWT decoding failed")
        raise credentials_exception

    user = get_user_by_username(db, username)
    if user is None:
        logger.debug("JWT valid but no matching user: %s", username)
        raise credentials_exception
    # Tokens from before a password change carry an older version (or none)
    if payload.get("tv", 0) != (user.token_version or 0):
        logger.debug("JWT from before a password change: %s", username)
        raise credentials_exception
    return user


def get_optional_user(
    token=Depends(oauth2_optional), db: Session = Depends(get_db)
) -> User | None:
    """The logged-in user, or None when no token was sent.

    For routes that anybody may call but whose answer depends on who asks. A
    token that was sent must still be valid: a bad one is a 401, as anywhere.
    """
    if token is None:
        return None
    return get_current_user(token, db)


def require_global_role(*roles: str):
    """Dependency factory: the caller must hold at least one of `roles`.

    Global roles are independent of each other: being an admin does not make
    somebody a train admin. Routes that should accept both list both.
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not any(current_user.has_global_role(role) for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You lack the server-wide role for this action",
            )
        return current_user

    return dependency
