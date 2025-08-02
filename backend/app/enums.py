from enum import Enum


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
