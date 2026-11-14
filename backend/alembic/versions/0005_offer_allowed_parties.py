"""offers: allowed_user_ids / allowed_faction_ids / is_private replace allowed_parties

allowed_parties was never read by the application (its meaning was never
defined), so its values are dropped rather than converted.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-14 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("offers") as batch_op:
        batch_op.add_column(sa.Column("allowed_user_ids", sa.JSON, nullable=True))
        batch_op.add_column(sa.Column("allowed_faction_ids", sa.JSON, nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_private",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.create_index("ix_offers_is_private", ["is_private"])
        batch_op.drop_column("allowed_parties")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("offers") as batch_op:
        batch_op.add_column(sa.Column("allowed_parties", sa.JSON, nullable=True))
        batch_op.drop_index("ix_offers_is_private")
        batch_op.drop_column("is_private")
        batch_op.drop_column("allowed_faction_ids")
        batch_op.drop_column("allowed_user_ids")
