"""new members join as "Membre": the "Invité" role goes

Revision ID: 0023
Revises: 0022
Create Date: 2026-11-22 23:00:00.000000

Joining a faction (freely, or through an accepted join request) used to give
the "Invité" role, with no permission at all, until somebody changed it. New
members now get "Membre", and "Invité" is no longer created with a faction.

For every faction:
- a "Membre" role is created if it has none (deleted or renamed: it wasn't
  protected until now), with the default permissions;
- its "Invité" members become "Membre", and its "Invité" role is deleted.

Downgrade: an "Invité" role is created again in every faction (empty: who
was a guest is not known any more).
"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0023"
down_revision: Union[str, Sequence[str], None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MEMBER = "Membre"
GUEST = "Invité"
PERMISSIONS = (
    "accept_offers",
    "create_offers",
    "manage_funds",
    "handle_members",
    "manage_roles",
    "manage_docs",
    "manage_trains",
    "manage_territory",
    "view_transactions",
)


def _insert_role(conn, faction_id: int, name: str, description: str, **granted):
    now = datetime.utcnow()
    values = {p: bool(granted.get(p, False)) for p in PERMISSIONS}
    columns = ", ".join(PERMISSIONS)
    params = ", ".join(f":{p}" for p in PERMISSIONS)
    conn.execute(
        sa.text(
            f"INSERT INTO roles (name, description, faction_id, {columns}, "
            f"created_at, updated_at) VALUES (:name, :description, "
            f":faction_id, {params}, :now, :now)"
        ),
        {
            "name": name,
            "description": description,
            "faction_id": faction_id,
            "now": now,
            **values,
        },
    )


def _role_ids(conn, faction_id: int, name: str) -> list[int]:
    return [
        row[0]
        for row in conn.execute(
            sa.text(
                "SELECT role_id FROM roles WHERE faction_id = :f AND name = :n "
                "ORDER BY role_id"
            ),
            {"f": faction_id, "n": name},
        )
    ]


def upgrade() -> None:
    conn = op.get_bind()
    faction_ids = [r[0] for r in conn.execute(sa.text("SELECT faction_id FROM factions"))]
    for faction_id in faction_ids:
        members = _role_ids(conn, faction_id, MEMBER)
        if not members:
            _insert_role(
                conn, faction_id, MEMBER, "Membre normal", view_transactions=True
            )
            members = _role_ids(conn, faction_id, MEMBER)
        member = members[0]

        for guest in _role_ids(conn, faction_id, GUEST):
            conn.execute(
                sa.text("UPDATE users SET role_id = :m WHERE role_id = :g"),
                {"m": member, "g": guest},
            )
            conn.execute(
                sa.text("DELETE FROM roles WHERE role_id = :g"), {"g": guest}
            )


def downgrade() -> None:
    conn = op.get_bind()
    faction_ids = [r[0] for r in conn.execute(sa.text("SELECT faction_id FROM factions"))]
    for faction_id in faction_ids:
        if not _role_ids(conn, faction_id, GUEST):
            _insert_role(conn, faction_id, GUEST, "Souhaite rejoindre la faction")
