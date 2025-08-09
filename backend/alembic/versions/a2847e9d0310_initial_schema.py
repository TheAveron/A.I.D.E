"""Initial schema

Revision ID: a2847e9d0310
Revises:
Create Date: 2025-08-09 12:55:33.951025

"""

from enum import Enum
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2847e9d0310"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class OfferTypeEnum(Enum):
    """Type of offer: buy or sell."""

    BUY = "BUY"
    SELL = "SELL"


class OfferStatusEnum(str, Enum):
    """Status of the offer."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class OfferActionEnum(str, Enum):
    """Possible actions recorded in the offer history."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    ACCEPTED = "ACCEPTED"
    CANCELLED = "CANCELLED"


def upgrade():
    # Create ENUM types
    offer_type_enum = postgresql.ENUM(
        *[e.value for e in OfferTypeEnum], name="offer_type_enum"
    )
    # offer_type_enum.create(op.get_bind(), checkfirst=True)

    offer_status_enum = postgresql.ENUM(
        *[e.value for e in OfferStatusEnum], name="offer_status_enum"
    )
    # offer_status_enum.create(op.get_bind(), checkfirst=True)

    offer_action_enum = postgresql.ENUM(
        *[e.value for e in OfferActionEnum], name="offer_action_enum"
    )
    # offer_action_enum.create(op.get_bind(), checkfirst=True)

    # Create factions table
    op.create_table(
        "factions",
        sa.Column("faction_id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_approved", sa.Boolean, nullable=True, default=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    # Create currencies table
    op.create_table(
        "currencies",
        sa.Column("name", sa.String(length=50), primary_key=True, index=True),
        sa.Column(
            "faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id", ondelete="CASCADE"),
            nullable=True,
            unique=True,
            index=True,
        ),
        sa.Column("symbol", sa.String(length=10), nullable=True),
        sa.Column("total_in_circulation", sa.Integer, nullable=False, default=0),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    # Create roles table
    op.create_table(
        "roles",
        sa.Column("role_id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("accept_offers", sa.Boolean, nullable=False, default=False),
        sa.Column("create_offers", sa.Boolean, nullable=False, default=False),
        sa.Column("manage_funds", sa.Boolean, nullable=False, default=False),
        sa.Column("handle_members", sa.Boolean, nullable=False, default=False),
        sa.Column("manage_roles", sa.Boolean, nullable=False, default=False),
        sa.Column("manage_docs", sa.Boolean, nullable=False, default=False),
        sa.Column("view_transactions", sa.Boolean, nullable=False, default=False),
        sa.Column(
            "faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("faction_id", "name", name="uq_faction_role_name"),
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer, primary_key=True),
        sa.Column("is_admin", sa.Boolean, nullable=False, default=False),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("email", sa.String(length=120), nullable=True, unique=True),
        sa.Column("hashed_password", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id"),
            nullable=True,
        ),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.role_id"), nullable=True),
        sa.Index("ix_users_username_email", "username", "email"),
    )

    # Create offers table
    op.create_table(
        "offers",
        sa.Column("offer_id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.user_id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id"),
            nullable=True,
            index=True,
        ),
        sa.Column("offer_type", offer_type_enum, nullable=False, index=True),
        sa.Column("item_description", sa.String, nullable=False),
        sa.Column(
            "currency_name",
            sa.String(length=50),
            sa.ForeignKey("currencies.name"),
            nullable=False,
            index=True,
        ),
        sa.Column("price_per_unit", sa.Float, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("init_quantity", sa.Integer, nullable=False),
        sa.Column("allowed_parties", sa.JSON, nullable=True),
        sa.Column(
            "status", offer_status_enum, nullable=False, default="open", index=True
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "accepted_by_user_id",
            sa.Integer,
            sa.ForeignKey("users.user_id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "accepted_by_faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id"),
            nullable=True,
            index=True,
        ),
        sa.CheckConstraint(
            "(user_id IS NOT NULL AND faction_id IS NULL) OR (user_id IS NULL AND faction_id IS NOT NULL)",
            name="check_only_one_creator",
        ),
        sa.Index("ix_offers_status_type", "status", "offer_type"),
    )

    # Create offer_history table
    op.create_table(
        "offer_history",
        sa.Column("history_id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "offer_id",
            sa.Integer,
            sa.ForeignKey("offers.offer_id"),
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
        sa.Column(
            "actor_faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id"),
            nullable=True,
            index=True,
        ),
        sa.Column("action", offer_action_enum, nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("notes", sa.String, nullable=True),
        sa.CheckConstraint(
            "(actor_user_id IS NOT NULL AND actor_faction_id IS NULL) OR (actor_user_id IS NULL AND actor_faction_id IS NOT NULL)",
            name="check_only_one_actor",
        ),
        sa.Index("ix_offer_history_offer_id_timestamp", "offer_id", "timestamp"),
    )

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column("transaction_id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "offer_id",
            sa.Integer,
            sa.ForeignKey("offers.offer_id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "buyer_user_id",
            sa.Integer,
            sa.ForeignKey("users.user_id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "buyer_faction_id",
            sa.Integer,
            sa.ForeignKey("factions.faction_id"),
            nullable=True,
            index=True,
        ),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "currency_name",
            sa.String(length=50),
            sa.ForeignKey("currencies.name"),
            nullable=False,
        ),
        sa.Column(
            "timestamp", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.CheckConstraint(
            "(buyer_user_id IS NOT NULL AND buyer_faction_id IS NULL) OR (buyer_user_id IS NULL AND buyer_faction_id IS NOT NULL)",
            name="check_only_one_buyer",
        ),
        sa.Index("ix_transactions_offer_id_timestamp", "offer_id", "timestamp"),
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table("transactions")
    op.drop_table("offer_history")
    op.drop_table("offers")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("currencies")
    op.drop_table("factions")

    # Drop ENUM types
    offer_action_enum = postgresql.ENUM(name="offer_action_enum")
    offer_action_enum.drop(op.get_bind(), checkfirst=True)

    offer_status_enum = postgresql.ENUM(name="offer_status_enum")
    offer_status_enum.drop(op.get_bind(), checkfirst=True)

    offer_type_enum = postgresql.ENUM(name="offer_type_enum")
    offer_type_enum.drop(op.get_bind(), checkfirst=True)
