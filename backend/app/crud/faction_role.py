from sqlalchemy.orm import Session

from database import Role


def get_role_by_id(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str):
    return db.query(Role).filter(Role.name == name).first()


def create_role(db: Session, name: str, description: str | None = None):
    role = Role(name=name, description=description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(
    db: Session, role_id: int, name: str | None = None, description: str | None = None
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return None
    if name is not None:
        role.name = name  # type: ignore
    if description is not None:
        role.description = description  # type: ignore
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: int):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return None
    db.delete(role)
    db.commit()
    return True
