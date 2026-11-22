from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import Role, User
from ..misc import (DEPUTY_ROLE_NAME, LEADER_ROLE_NAME, MEMBER_ROLE_NAME,
                    FactionPermission)
from ..schemas import RoleCreate, RoleUpdate


def create_role(db: Session, faction_id: int, role_in: RoleCreate) -> Role:
    role = Role(
        name=role_in.name,
        description=role_in.description,
        faction_id=faction_id,
        accept_offers=role_in.accept_offers,
        create_offers=role_in.create_offers,
        manage_funds=role_in.manage_funds,
        handle_members=role_in.handle_members,
        manage_roles=role_in.manage_roles,
        manage_docs=role_in.manage_docs,
        manage_trains=role_in.manage_trains,
        manage_territory=role_in.manage_territory,
        view_transactions=role_in.view_transactions,
    )
    db.add(role)
    _commit_unique_role(db)
    db.refresh(role)
    return role


def _commit_unique_role(db: Session) -> None:
    """Commit, turning a (faction, name) clash into a 409 instead of a 500."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A role with this name already exists in this faction",
        )


def get_roles_by_faction(db: Session, faction_id: int) -> list[Role]:
    return db.query(Role).filter(Role.faction_id == faction_id).all()


def get_role_by_id(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.role_id == role_id).first()


def update_role(db: Session, role: Role, role_update: RoleUpdate) -> Role:
    for field, value in role_update.model_dump(exclude_unset=True).items():
        setattr(role, field, value)

    _commit_unique_role(db)
    db.refresh(role)
    return role


def count_role_members(db: Session, role_id: int) -> int:
    return db.query(User).filter(User.role_id == role_id).count()


def delete_role(db: Session, role: Role) -> None:
    if count_role_members(db, role.role_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This role is still assigned to members",
        )
    db.delete(role)
    db.commit()


def create_default_faction_roles(
    db: Session, faction_id: int, user_id: int, commit: bool = True
):
    """
    Create a set of default roles for a newly created faction with predefined permissions.

    The user `user_id` becomes the faction's leader (role "Chef"). With
    `commit=False` nothing is committed, so the caller can make this part of a
    larger transaction.
    """

    default_roles = [
        {
            "name": LEADER_ROLE_NAME,
            "description": "Chef de la faction avec toutes les permissions.",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: True,
                FactionPermission.CREATE_OFFERS: True,
                FactionPermission.MANAGE_FUNDS: True,
                FactionPermission.HANDLE_MEMBERS: True,
                FactionPermission.MANAGE_ROLES: True,
                FactionPermission.MANAGE_DOCS: True,
                FactionPermission.MANAGE_TRAINS: True,
                FactionPermission.MANAGE_TERRITORY: True,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": DEPUTY_ROLE_NAME,
            "description": "Adjoint du chef, l'aide à administrer la faction",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: True,
                FactionPermission.CREATE_OFFERS: True,
                FactionPermission.MANAGE_FUNDS: False,
                FactionPermission.HANDLE_MEMBERS: True,
                FactionPermission.MANAGE_ROLES: True,
                FactionPermission.MANAGE_DOCS: True,
                FactionPermission.MANAGE_TRAINS: True,
                FactionPermission.MANAGE_TERRITORY: True,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": "Trésorier",
            "description": "Gère la monnaie et les transactions.",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: False,
                FactionPermission.CREATE_OFFERS: False,
                FactionPermission.MANAGE_FUNDS: True,
                FactionPermission.HANDLE_MEMBERS: False,
                FactionPermission.MANAGE_ROLES: False,
                FactionPermission.MANAGE_DOCS: False,
                FactionPermission.MANAGE_TRAINS: False,
                FactionPermission.MANAGE_TERRITORY: False,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": "Marchand",
            "description": "Peut créer et accepter des offres.",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: True,
                FactionPermission.CREATE_OFFERS: True,
                FactionPermission.MANAGE_FUNDS: False,
                FactionPermission.HANDLE_MEMBERS: False,
                FactionPermission.MANAGE_ROLES: False,
                FactionPermission.MANAGE_DOCS: False,
                FactionPermission.MANAGE_TRAINS: False,
                FactionPermission.MANAGE_TERRITORY: False,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": MEMBER_ROLE_NAME,
            "description": "Membre normal",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: False,
                FactionPermission.CREATE_OFFERS: False,
                FactionPermission.MANAGE_FUNDS: False,
                FactionPermission.HANDLE_MEMBERS: False,
                FactionPermission.MANAGE_ROLES: False,
                FactionPermission.MANAGE_DOCS: False,
                FactionPermission.MANAGE_TRAINS: False,
                FactionPermission.MANAGE_TERRITORY: False,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
    ]

    for role_data in default_roles:
        db_role = Role(
            name=role_data["name"],
            description=role_data["description"],
            faction_id=faction_id,
            accept_offers=role_data["permissions"][FactionPermission.ACCEPT_OFFERS],
            create_offers=role_data["permissions"][FactionPermission.CREATE_OFFERS],
            manage_funds=role_data["permissions"][FactionPermission.MANAGE_FUNDS],
            handle_members=role_data["permissions"][FactionPermission.HANDLE_MEMBERS],
            manage_roles=role_data["permissions"][FactionPermission.MANAGE_ROLES],
            manage_docs=role_data["permissions"][FactionPermission.MANAGE_DOCS],
            manage_trains=role_data["permissions"][FactionPermission.MANAGE_TRAINS],
            manage_territory=role_data["permissions"][
                FactionPermission.MANAGE_TERRITORY
            ],
            view_transactions=role_data["permissions"][
                FactionPermission.VIEW_TRANSACTIONS
            ],
        )
        db.add(db_role)
        db.flush()  # assigns role_id

        if db_role.name == LEADER_ROLE_NAME:
            leader = db.query(User).filter(User.user_id == user_id).first()
            if leader:
                leader.faction_id = faction_id
                leader.role_id = db_role.role_id

    if commit:
        db.commit()
