"""offers.expires_at, and the cancellation of transactions

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-16 11:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("offers", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.create_index("ix_offers_expires_at", "offers", ["expires_at"])

    op.add_column("transactions", sa.Column("quantity", sa.Integer(), nullable=True))
    op.add_column(
        "transactions", sa.Column("cancelled_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "transactions",
        sa.Column("cancelled_by_name", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("cancel_reason", sa.String(length=300), nullable=True),
    )
    op.create_index("ix_transactions_cancelled_at", "transactions", ["cancelled_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_transactions_cancelled_at", table_name="transactions")
    op.drop_column("transactions", "cancel_reason")
    op.drop_column("transactions", "cancelled_by_name")
    op.drop_column("transactions", "cancelled_at")
    op.drop_column("transactions", "quantity")
    op.drop_index("ix_offers_expires_at", table_name="offers")
    op.drop_column("offers", "expires_at")
