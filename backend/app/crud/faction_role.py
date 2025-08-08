from typing import Optional

from sqlalchemy.orm import Session

from backend.app.crud.user import update_user_faction_and_role

from ..database import Role
from ..misc import FactionPermission
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
        view_transactions=role_in.view_transactions,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def get_roles_by_faction(db: Session, faction_id: int) -> list[Role]:
    return db.query(Role).filter(Role.faction_id == faction_id).all()


def get_role_by_id(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.role_id == role_id).first()


def update_role(db: Session, role: Role, role_update: RoleUpdate) -> Role:
    for field, value in role_update.dict(exclude_unset=True).items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role: Role) -> None:
    db.delete(role)
    db.commit()


def create_default_faction_roles(db: Session, faction_id: int, user_id: int):
    """
    Create a set of default roles for a newly created faction with predefined permissions.
    """

    default_roles = [
        {
            "name": "Chef",
            "description": "Chef de la faction avec toutes les permissions.",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: True,
                FactionPermission.CREATE_OFFERS: True,
                FactionPermission.MANAGE_FUNDS: True,
                FactionPermission.HANDLE_MEMBERS: True,
                FactionPermission.MANAGE_ROLES: True,
                FactionPermission.MANAGE_DOCS: True,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": "Chef Adjoint",
            "description": "Adjoint du chef, l'aide à administrer la faction",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: True,
                FactionPermission.CREATE_OFFERS: True,
                FactionPermission.MANAGE_FUNDS: False,
                FactionPermission.HANDLE_MEMBERS: True,
                FactionPermission.MANAGE_ROLES: True,
                FactionPermission.MANAGE_DOCS: True,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": "Trésorier",
            "description": "Gère la monaie et les transactions.",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: False,
                FactionPermission.CREATE_OFFERS: False,
                FactionPermission.MANAGE_FUNDS: True,
                FactionPermission.HANDLE_MEMBERS: False,
                FactionPermission.MANAGE_ROLES: False,
                FactionPermission.MANAGE_DOCS: False,
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
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": "Membre",
            "description": "Membre normal",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: False,
                FactionPermission.CREATE_OFFERS: False,
                FactionPermission.MANAGE_FUNDS: False,
                FactionPermission.HANDLE_MEMBERS: False,
                FactionPermission.MANAGE_ROLES: False,
                FactionPermission.MANAGE_DOCS: False,
                FactionPermission.VIEW_TRANSACTIONS: True,
            },
        },
        {
            "name": "Invité",
            "description": "Souhaite rejoindre la faction",
            "permissions": {
                FactionPermission.ACCEPT_OFFERS: False,
                FactionPermission.CREATE_OFFERS: False,
                FactionPermission.MANAGE_FUNDS: False,
                FactionPermission.HANDLE_MEMBERS: False,
                FactionPermission.MANAGE_ROLES: False,
                FactionPermission.MANAGE_DOCS: False,
                FactionPermission.VIEW_TRANSACTIONS: False,
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
            view_transactions=role_data["permissions"][
                FactionPermission.VIEW_TRANSACTIONS
            ],
        )
        db.add(db_role)
        db.commit()

        if db_role.name == "Chef":
            update_user_faction_and_role(db, user_id, faction_id, db_role.role_id)
