"""user_global_roles: server-wide roles moved out of users.is_admin

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-15 15:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_global_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role"),
    )
    # Existing admins keep their rights.
    op.execute(
        "INSERT INTO user_global_roles (user_id, role, granted_at) "
        "SELECT user_id, 'admin', CURRENT_TIMESTAMP FROM users WHERE is_admin"
    )
    op.drop_column("users", "is_admin")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute(
        "UPDATE users SET is_admin = TRUE WHERE user_id IN "
        "(SELECT user_id FROM user_global_roles WHERE role = 'admin')"
    )
    op.drop_table("user_global_roles")
