"""trains: lines, stops, trains, history, manage_trains permission

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-15 17:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, Sequence[str], None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "roles",
        sa.Column(
            "manage_trains", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    # Leaders and their deputies manage trains from the start
    op.execute(
        "UPDATE roles SET manage_trains = TRUE WHERE name IN ('Chef', 'Chef Adjoint')"
    )

    op.create_table(
        "lines",
        sa.Column("line_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=2), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_faction_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_faction_id"], ["factions.faction_id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("line_id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "line_stops",
        sa.Column("stop_id", sa.Integer(), nullable=False),
        sa.Column("line_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["lines.line_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["station_id"], ["stations.station_id"]),
        sa.PrimaryKeyConstraint("stop_id"),
        sa.UniqueConstraint("line_id", "station_id", name="uq_line_stop_station"),
    )
    op.create_index("ix_line_stops_line_id", "line_stops", ["line_id"])
    op.create_index("ix_line_stops_station_id", "line_stops", ["station_id"])

    op.create_table(
        "trains",
        sa.Column("train_id", sa.Integer(), nullable=False),
        sa.Column("line_id", sa.Integer(), nullable=False),
        sa.Column("service", sa.String(length=1), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("common_name", sa.String(length=24), nullable=True),
        sa.Column("legacy_id", sa.String(length=50), nullable=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("owner_faction_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "(owner_user_id IS NOT NULL AND owner_faction_id IS NULL) OR "
            "(owner_user_id IS NULL AND owner_faction_id IS NOT NULL)",
            name="check_train_one_owner",
        ),
        sa.CheckConstraint("number BETWEEN 1 AND 99", name="check_train_number"),
        sa.ForeignKeyConstraint(["line_id"], ["lines.line_id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["owner_faction_id"], ["factions.faction_id"]),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("train_id"),
    )
    op.create_index("ix_trains_line_id", "trains", ["line_id"])
    op.create_index("ix_trains_owner_user_id", "trains", ["owner_user_id"])
    op.create_index("ix_trains_owner_faction_id", "trains", ["owner_faction_id"])
    op.create_index(
        "uq_trains_active_line_number",
        "trains",
        ["line_id", "number"],
        unique=True,
        postgresql_where=sa.text("retired_at IS NULL"),
    )
    op.create_index(
        "uq_trains_active_legacy_id",
        "trains",
        ["legacy_id"],
        unique=True,
        postgresql_where=sa.text("retired_at IS NULL AND legacy_id IS NOT NULL"),
    )

    op.create_table(
        "train_history",
        sa.Column("history_id", sa.Integer(), nullable=False),
        sa.Column("train_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=10), nullable=False),
        sa.Column("old_name", sa.String(length=60), nullable=True),
        sa.Column("new_name", sa.String(length=60), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["train_id"], ["trains.train_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("history_id"),
    )
    op.create_index("ix_train_history_train_id", "train_history", ["train_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_train_history_train_id", table_name="train_history")
    op.drop_table("train_history")
    op.drop_index("uq_trains_active_legacy_id", table_name="trains")
    op.drop_index("uq_trains_active_line_number", table_name="trains")
    op.drop_index("ix_trains_owner_faction_id", table_name="trains")
    op.drop_index("ix_trains_owner_user_id", table_name="trains")
    op.drop_index("ix_trains_line_id", table_name="trains")
    op.drop_table("trains")
    op.drop_index("ix_line_stops_station_id", table_name="line_stops")
    op.drop_index("ix_line_stops_line_id", table_name="line_stops")
    op.drop_table("line_stops")
    op.drop_table("lines")
    op.drop_column("roles", "manage_trains")
