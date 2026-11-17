"""stations and platforms

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-15 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, Sequence[str], None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "stations",
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=True),
        sa.Column("z", sa.Integer(), nullable=False),
        sa.Column("dimension", sa.String(length=20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("station_id"),
    )
    op.create_index(
        "uq_stations_name_lower",
        "stations",
        [sa.text("lower(name)")],
        unique=True,
    )
    op.create_table(
        "platforms",
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.ForeignKeyConstraint(
            ["station_id"], ["stations.station_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("platform_id"),
        sa.UniqueConstraint("station_id", "name", name="uq_platform_station_name"),
    )
    op.create_index("ix_platforms_station_id", "platforms", ["station_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_platforms_station_id", table_name="platforms")
    op.drop_table("platforms")
    op.drop_index("uq_stations_name_lower", table_name="stations")
    op.drop_table("stations")
