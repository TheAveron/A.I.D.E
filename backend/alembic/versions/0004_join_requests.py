"""join requests and factions.requires_approval

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-13 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("factions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "requires_approval",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    op.create_table(
        "join_requests",
        sa.Column("request_id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False
        ),
        sa.Column(
            "faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column(
            "decided_by_user_id",
            sa.Integer,
            sa.ForeignKey("users.user_id"),
            nullable=True,
        ),
    )
    op.create_index("ix_join_requests_user_id", "join_requests", ["user_id"])
    op.create_index("ix_join_requests_faction_id", "join_requests", ["faction_id"])
    op.create_index(
        "uq_join_requests_one_pending_per_user",
        "join_requests",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDING'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("join_requests")
    with op.batch_alter_table("factions") as batch_op:
        batch_op.drop_column("requires_approval")
