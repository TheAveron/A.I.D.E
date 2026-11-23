"""The staff audit trail.

`record` never commits: an entry belongs to the transaction of the action it
reports, so it exists exactly when the action does.
"""

from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

from ..database import AuditLog, User


class AuditAction(str, Enum):
    ROLE_GRANTED = "role_granted"
    ROLE_REVOKED = "role_revoked"
    PASSWORD_RESET = "password_reset"
    USER_REMOVED_FROM_FACTION = "user_removed_from_faction"
    FACTION_APPROVED = "faction_approved"
    FACTION_UNAPPROVED = "faction_unapproved"
    FACTION_DELETED = "faction_deleted"
    # The market
    OFFER_CANCELLED = "offer_cancelled"
    TRANSACTION_CANCELLED = "transaction_cancelled"
    CURRENCY_CREATED = "currency_created"
    CURRENCY_CHANGED = "currency_changed"
    CURRENCY_DELETED = "currency_deleted"
    # Money admins acting on currencies their faction does not issue
    CURRENCY_FACTION_ADDED = "currency_faction_added"
    CURRENCY_FACTION_REMOVED = "currency_faction_removed"
    CURRENCY_ISSUER_CHANGED = "currency_issuer_changed"
    # Admins acting on the territories and markers of others
    TERRITORY_CHANGED = "territory_changed"
    TERRITORY_DELETED = "territory_deleted"
    MARKER_CHANGED = "marker_changed"
    MARKER_DELETED = "marker_deleted"
    # Train admins acting on what belongs to somebody else
    TRAIN_CHANGED = "train_changed"
    TRAIN_RETIRED = "train_retired"
    LINE_CHANGED = "line_changed"
    LINE_DELETED = "line_deleted"
    STATION_CHANGED = "station_changed"
    STATION_DELETED = "station_deleted"
    # Schematics: train admins checking them against the railway standards,
    # admins changing or deleting those of others
    SCHEMATIC_COMPLIANCE = "schematic_compliance"
    SCHEMATIC_CHANGED = "schematic_changed"
    SCHEMATIC_DELETED = "schematic_deleted"


# What a train admin (who is not an admin) is allowed to read in the trail
TRAIN_TARGETS = ("train", "line", "station", "schematic")
# ... and a money admin
MONEY_TARGETS = ("currency",)


def record(
    db: Session,
    actor: User,
    action: AuditAction,
    target_type: str,
    target_id: Optional[int] = None,
    target_name: Optional[str] = None,
    detail: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor.user_id,
        actor_name=actor.username[:50],
        action=action.value,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name[:100] if target_name else None,
        detail=detail[:300] if detail else None,
    )
    db.add(entry)
    return entry
