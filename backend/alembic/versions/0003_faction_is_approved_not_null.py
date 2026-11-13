"""factions.is_approved NOT NULL

The model declares the column as a plain bool (never NULL) but the initial
schema created it nullable; `alembic check` reported the difference.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-13 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # A NULL means "not approved" everywhere in the code.
    op.execute("UPDATE factions SET is_approved = false WHERE is_approved IS NULL")
    with op.batch_alter_table("factions") as batch_op:
        batch_op.alter_column("is_approved", existing_type=sa.Boolean(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("factions") as batch_op:
        batch_op.alter_column("is_approved", existing_type=sa.Boolean(), nullable=True)
