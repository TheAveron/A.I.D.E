"""add currency_history

Revision ID: c7d4e91b2a55
Revises: 0001
Create Date: 2026-09-28 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d4e91b2a55"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "currency_history",
        sa.Column("history_id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "currency_name",
            sa.String(length=50),
            sa.ForeignKey("currencies.name"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "actor_user_id",
            sa.Integer,
            sa.ForeignKey("users.user_id"),
            nullable=True,
            index=True,
        ),
        sa.Column("old_total_in_circulation", sa.Integer, nullable=False),
        sa.Column("new_total_in_circulation", sa.Integer, nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("notes", sa.String, nullable=True),
        sa.Index(
            "ix_currency_history_currency_name_timestamp",
            "currency_name",
            "timestamp",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("currency_history")
