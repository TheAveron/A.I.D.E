"""map territories and markers, manage_territory permission

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-16 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015"
down_revision: Union[str, Sequence[str], None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "roles",
        sa.Column(
            "manage_territory", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    # Leaders and their deputies draw their faction's land from the start
    op.execute(
        "UPDATE roles SET manage_territory = TRUE "
        "WHERE name IN ('Chef', 'Chef Adjoint')"
    )

    op.create_table(
        "map_territories",
        sa.Column("territory_id", sa.Integer(), nullable=False),
        sa.Column("map_name", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("faction_id", sa.Integer(), nullable=False),
        sa.Column("points", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["faction_id"], ["factions.faction_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("territory_id"),
        sa.UniqueConstraint("map_name", "faction_id", "name", name="uq_territory_name"),
    )
    op.create_index("ix_map_territories_map_name", "map_territories", ["map_name"])
    op.create_index("ix_map_territories_faction_id", "map_territories", ["faction_id"])

    op.create_table(
        "map_markers",
        sa.Column("marker_id", sa.Integer(), nullable=False),
        sa.Column("map_name", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("z", sa.Integer(), nullable=False),
        sa.Column("faction_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(faction_id IS NOT NULL AND user_id IS NULL) OR "
            "(faction_id IS NULL AND user_id IS NOT NULL)",
            name="ck_map_marker_one_owner",
        ),
        sa.ForeignKeyConstraint(
            ["faction_id"], ["factions.faction_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("marker_id"),
    )
    op.create_index("ix_map_markers_map_name", "map_markers", ["map_name"])
    op.create_index("ix_map_markers_faction_id", "map_markers", ["faction_id"])
    op.create_index("ix_map_markers_user_id", "map_markers", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("map_markers")
    op.drop_table("map_territories")
    op.drop_column("roles", "manage_territory")
