"""seed_data

Revision ID: 0001
Revises: a2847e9d0310
Create Date: 2025-08-09 15:28:48.128669

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.orm import Session

from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = "a2847e9d0310"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    now = datetime.utcnow()

    default_roles = [
        {
            "name": "Chef",
            "description": "Chef de la faction avec toutes les permissions.",
            "permissions": {
                "accept_offers": True,
                "create_offers": True,
                "manage_funds": True,
                "handle_members": True,
                "manage_roles": True,
                "manage_docs": True,
                "view_transactions": True,
            },
        },
        {
            "name": "Chef Adjoint",
            "description": "Adjoint du chef, l'aide � administrer la faction",
            "permissions": {
                "accept_offers": True,
                "create_offers": True,
                "manage_funds": False,
                "handle_members": True,
                "manage_roles": True,
                "manage_docs": True,
                "view_transactions": True,
            },
        },
        {
            "name": "Tr�sorier",
            "description": "G�re la monaie et les transactions.",
            "permissions": {
                "accept_offers": False,
                "create_offers": False,
                "manage_funds": True,
                "handle_members": False,
                "manage_roles": False,
                "manage_docs": False,
                "view_transactions": True,
            },
        },
        {
            "name": "Marchand",
            "description": "Peut cr�er et accepter des offres.",
            "permissions": {
                "accept_offers": True,
                "create_offers": True,
                "manage_funds": False,
                "handle_members": False,
                "manage_roles": False,
                "manage_docs": False,
                "view_transactions": True,
            },
        },
        {
            "name": "Membre",
            "description": "Membre normal",
            "permissions": {
                "accept_offers": False,
                "create_offers": False,
                "manage_funds": False,
                "handle_members": False,
                "manage_roles": False,
                "manage_docs": False,
                "view_transactions": True,
            },
        },
        {
            "name": "Invit�",
            "description": "Souhaite rejoindre la faction",
            "permissions": {
                "accept_offers": False,
                "create_offers": False,
                "manage_funds": False,
                "handle_members": False,
                "manage_roles": False,
                "manage_docs": False,
                "view_transactions": False,
            },
        },
    ]

    faction_id = session.execute(
        sa.text(
            """
            INSERT INTO factions (name, description, is_approved, created_at, updated_at)
            VALUES (:name, :description, :is_approved, :created_at, :updated_at)
            RETURNING faction_id
        """
        ),
        {
            "name": "Sans Faction",
            "description": "",
            "is_approved": True,
            "created_at": now,
            "updated_at": now,
        },
    ).scalar()

    chef_role_id = None
    for role in default_roles:
        role_id = session.execute(
            sa.text(
                """
                INSERT INTO roles (
                    name, description,
                    accept_offers, create_offers, manage_funds,
                    handle_members, manage_roles, manage_docs, view_transactions,
                    faction_id, created_at, updated_at
                )
                VALUES (
                    :name, :description,
                    :accept_offers, :create_offers, :manage_funds,
                    :handle_members, :manage_roles, :manage_docs, :view_transactions,
                    :faction_id, :created_at, :updated_at
                )
                RETURNING role_id
            """
            ),
            {
                "name": role["name"],
                "description": role["description"],
                "accept_offers": role["permissions"]["accept_offers"],
                "create_offers": role["permissions"]["create_offers"],
                "manage_funds": role["permissions"]["manage_funds"],
                "handle_members": role["permissions"]["handle_members"],
                "manage_roles": role["permissions"]["manage_roles"],
                "manage_docs": role["permissions"]["manage_docs"],
                "view_transactions": role["permissions"]["view_transactions"],
                "faction_id": faction_id,
                "created_at": now,
                "updated_at": now,
            },
        ).scalar()

        if role["name"] == "Chef":
            chef_role_id = role_id

    hashed_pw = "$2b$12$WnEoMQQ9GtC7nLR9FsYWYeyu7NjY3XPER4pQ4tkJWOwbLYw8Y9/12"

    session.execute(
        sa.text(
            """
            INSERT INTO "users" (
                is_admin, username, email, hashed_password,
                created_at, updated_at, faction_id, role_id
            )
            VALUES (
                :is_admin, :username, :email, :hashed_password,
                :created_at, :updated_at, :faction_id, :role_id
            )
        """
        ),
        {
            "is_admin": True,
            "username": "ADmin_oP",
            "email": "",
            "hashed_password": hashed_pw,
            "created_at": now,
            "updated_at": now,
            "faction_id": faction_id,
            "role_id": chef_role_id,
        },
    )

    session.commit()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    session.execute(
        sa.text("""DELETE FROM "users" WHERE username = :username"""),
        {"username": "ADmin_oP"},
    )
    session.execute(
        sa.text(
            """DELETE FROM roles WHERE faction_id IN (SELECT faction_id FROM faction WHERE name = :name)"""
        ),
        {"name": "Sans Faction"},
    )
    session.execute(
        sa.text("""DELETE FROM factions WHERE name = :name"""), {"name": "Sans Faction"}
    )
    session.commit()
