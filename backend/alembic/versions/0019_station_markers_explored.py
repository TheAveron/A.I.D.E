"""station markers become stations; structures can be marked as explored

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-22 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019"
down_revision: Union[str, Sequence[str], None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _dimension(map_name: str) -> str:
    # Same rule as the front (types/map.tsx): the first letter of the folder
    if map_name.startswith("N"):
        return "nether"
    if map_name.startswith("E"):
        return "end"
    return "overworld"


def upgrade() -> None:
    op.add_column(
        "map_markers",
        sa.Column("explored", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "map_markers", sa.Column("explored_by_user_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_map_markers_explored_by",
        "map_markers",
        "users",
        ["explored_by_user_id"],
        ["user_id"],
        ondelete="SET NULL",
    )
    op.add_column("map_markers", sa.Column("explored_at", sa.DateTime(), nullable=True))

    # A station placed from the map was only a marker: it showed nowhere in
    # the index of stations. It becomes a real station; one whose name is
    # already taken stays on the map as a plain point (nothing is lost).
    bind = op.get_bind()
    markers = bind.execute(
        sa.text(
            "SELECT marker_id, map_name, label, description, x, z, user_id, "
            "created_at, updated_at FROM map_markers WHERE kind = 'station' "
            "ORDER BY marker_id"
        )
    ).fetchall()
    for m in markers:
        taken = bind.execute(
            sa.text("SELECT 1 FROM stations WHERE lower(name) = lower(:name)"),
            {"name": m.label},
        ).first()
        if taken:
            bind.execute(
                sa.text("UPDATE map_markers SET kind = 'generic' WHERE marker_id = :id"),
                {"id": m.marker_id},
            )
            continue
        bind.execute(
            sa.text(
                "INSERT INTO stations (name, description, x, y, z, dimension, "
                "created_by_user_id, created_at, updated_at) VALUES "
                "(:name, :description, :x, NULL, :z, :dimension, :user_id, "
                ":created_at, :updated_at)"
            ),
            {
                "name": m.label,
                "description": m.description,
                "x": m.x,
                "z": m.z,
                "dimension": _dimension(m.map_name),
                # A faction's marker has no single author
                "user_id": m.user_id,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
            },
        )
        bind.execute(
            sa.text("DELETE FROM map_markers WHERE marker_id = :id"),
            {"id": m.marker_id},
        )


def downgrade() -> None:
    # The stations made from markers stay stations: they are real ones now
    op.drop_constraint(
        "fk_map_markers_explored_by", "map_markers", type_="foreignkey"
    )
    op.drop_column("map_markers", "explored_at")
    op.drop_column("map_markers", "explored_by_user_id")
    op.drop_column("map_markers", "explored")
