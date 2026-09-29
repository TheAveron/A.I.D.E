from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status

from .database.models.user import User


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
    MANAGE_DOCS = "manage_docs"
    VIEW_TRANSACTIONS = "view_transactions"


def check_faction_permission(
    user: User,
    permission: FactionPermission,
    target_faction_id: Optional[int] = None,
) -> None:
    """Raise 403 unless `user` holds `permission` in their own faction.

    When `target_faction_id` is given, also raise 403 if it isn't the
    user's own faction - this is what prevents a user with e.g.
    `manage_roles` in Faction A from editing Faction B's roles, just
    because they happen to know (or guess) Faction B's id. Every
    endpoint that acts on a specific faction's resource (a role, a
    currency, the faction itself) should pass its resolved faction_id
    here.
    """
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

    # A role only counts inside its own faction: a role_id pointing at
    # another faction's role (left over from older, unchecked updates) must
    # never grant anything here.
    if role.faction_id != user.faction_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your role does not belong to your faction",
        )

    if not role.has_permission(permission.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission for this action",
        )

    if target_faction_id is not None and user.faction_id != target_faction_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own faction's resources",
        )


def require_faction_permission(permission: FactionPermission):
    """FastAPI dependency factory for the common case where the target
    faction id is directly a `faction_id` path parameter on the route.

    Usage:
        @router.post("/faction/{faction_id}/create")
        def create_role(
            faction_id: int,
            ...,
            current_user: User = Depends(require_faction_permission(FactionPermission.MANAGE_ROLES)),
        ):
            ...

    For routes where the target faction can only be known after looking
    up the resource (e.g. a role_id or a currency_name), this factory
    doesn't apply - call check_faction_permission(...) directly in the
    route body instead, once the resource (and its faction_id) has been
    fetched.
    """

    # Deferred import: app.misc is imported very early (e.g. by
    # database/models/offer.py for OfferType/OfferStatus), and
    # app.core.security imports app.database, which imports the models
    # package, which imports app.misc again - a top-of-file import here
    # would be a circular import. By the time route modules call this
    # factory, app.core and app.database are already fully loaded, so a
    # local import here is safe.
    from .core.security import get_current_user

    def dependency(
        faction_id: int,
        current_user: User = Depends(get_current_user),
    ) -> User:
        check_faction_permission(current_user, permission, target_faction_id=faction_id)
        return current_user

    return dependency
