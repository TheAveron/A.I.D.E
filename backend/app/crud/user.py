from sqlalchemy.orm import Session

from ..core.security import verify_password
from ..database import User


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    username: str,
    hashed_password: str,
    faction_id: int | None = None,
    role_id: int | None = None,
    admin: bool = False,
):
    user = User(
        username=username,
        hashed_password=hashed_password,
        faction_id=faction_id,
        role_id=role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_faction_and_role(
    db: Session, user_id: int, faction_id: int | None, role_id: int | None
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    if faction_id is not None:
        user.faction_id = faction_id
    if role_id is not None:
        user.role_id = role_id

    db.commit()
    db.refresh(user)
    return user


def remove_user_faction_and_role(db: Session, user_id: int):
    return update_user_faction_and_role(db, user_id, None, None)


def user_has_faction(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.user_id == user_id).first()
    return bool(user and user.faction_id)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
