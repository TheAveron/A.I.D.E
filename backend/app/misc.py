from enum import Enum

from fastapi import HTTPException, status
from .database import User


class OfferType(str, Enum):
    """Type of offer: buy or sell."""

    BUY = "BUY"
    SELL = "SELL"


class OfferStatus(str, Enum):
    """Status of the offer."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class OfferAction(str, Enum):
    """Possible actions recorded in the offer history."""

    CREATED = "CREATED"
    UPDATED = "UPDATED"
    ACCEPTED = "ACCEPTED"
    CANCELLED = "CANCELLED"


class FactionPermission(str, Enum):
    """Possible permissions for faction members"""

    ACCEPT_OFFERS = "accept_offers"
    CREATE_OFFERS = "create_offers"
    MANAGE_FUNDS = "manage_funds"
    HANDLE_MEMBERS = "handle_members"
    MANAGE_ROLES = "manage_roles"
    VIEW_TRANSACTIONS = "view_transactions"


def check_faction_permission(user: User, permission: FactionPermission):
    """Raises HTTPException if the user doesn't have the required faction permission."""
    if not user.faction_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not in a faction"
        )

    role = user.role
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have no role in your faction",
        )

    if not role.has_permission(permission.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission for this action",
        )
