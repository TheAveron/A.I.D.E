"""Admin tools for the market: offers, transactions and currencies, and
read-only dumps of an account or a faction to debug what people report.

Every change here goes into the audit trail, and the people concerned are told.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core import require_global_role
from ..crud import audit
from ..crud import currencies as currency_crud
from ..crud import faction as faction_crud
from ..crud import offer as offer_crud
from ..crud.notification import members_with_permission, notify_many
from ..crud.offer_history import create_offer_history
from ..database import (
    Currency,
    Faction,
    GlobalRoleName,
    JoinRequest,
    Notification,
    Offer,
    Role,
    Train,
    Transaction,
    User,
    get_db,
)
from ..database.clock import utcnow
from ..misc import FactionPermission, OfferAction, OfferStatus
from ..schemas import (
    AdminCurrencyOut,
    AdminFactionOut,
    AdminFactionState,
    AdminOfferOut,
    AdminReason,
    AdminRoleState,
    AdminTransactionCancelled,
    AdminTransactionOut,
    AdminUserState,
    CurrencyCreate,
    CurrencyFactionOut,
    CurrencyUpdate,
)
from .admin import LEADER_ROLE_NAME, _admin_only, _escape_like, _target_user, _user_out

router = APIRouter(prefix="/admin", tags=["Administration"])


# ── Offers ────────────────────────────────────────────────────────────────


def _offer_out(offer: Offer) -> AdminOfferOut:
    if offer.user_id is not None:
        kind, owner_id = "user", offer.user_id
        owner_name = offer.user.username if offer.user else None
    else:
        kind, owner_id = "faction", offer.faction_id
        owner_name = offer.faction.name if offer.faction else None
    return AdminOfferOut(
        offer_id=offer.offer_id,
        offer_type=offer.offer_type.value,
        item_description=offer.item_description,
        currency_name=offer.currency_name,
        price_per_unit=offer.price_per_unit,
        quantity=offer.quantity,
        init_quantity=offer.init_quantity,
        status=offer.status.value,
        is_private=offer.is_private,
        owner_kind=kind,
        owner_id=owner_id,
        owner_name=owner_name,
        expires_at=offer.expires_at,
        created_at=offer.created_at,
    )


@router.get("/offers", response_model=list[AdminOfferOut])
def list_all_offers(
    state: str = Query("all", pattern="^(all|open|closed|cancelled)$"),
    q: Optional[str] = Query(None, max_length=100, description="Words in the item"),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Every offer, private ones included, newest first."""
    offer_crud.expire_overdue(db)
    query = db.query(Offer)
    if state != "all":
        query = query.filter(Offer.status == OfferStatus(state.upper()))
    if q and q.strip():
        query = query.filter(
            Offer.item_description.ilike(f"%{_escape_like(q)}%", escape="\\")
        )
    offers = (
        query.order_by(Offer.created_at.desc(), Offer.offer_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_offer_out(o) for o in offers]


@router.post("/offers/{offer_id}/cancel", response_model=AdminOfferOut)
def cancel_offer(
    offer_id: int,
    body: AdminReason,
    db: Session = Depends(get_db),
    admin: User = Depends(_admin_only),
):
    """Cancel an open offer, whoever owns it. Its owner is told why."""
    offer_crud.expire_overdue(db)
    offer = db.query(Offer).filter(Offer.offer_id == offer_id).with_for_update().first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.status != OfferStatus.OPEN:
        raise HTTPException(status_code=409, detail="Only open offers can be cancelled")

    offer.status = OfferStatus.CANCELLED
    offer.updated_at = utcnow()
    create_offer_history(
        db,
        offer.offer_id,
        OfferAction.CANCELLED,
        actor_user_id=admin.user_id,
        notes=f"Cancelled by an administrator: {body.reason}"[:500],
        commit=False,
    )
    audit.record(
        db,
        admin,
        audit.AuditAction.OFFER_CANCELLED,
        "offer",
        offer.offer_id,
        offer.item_description,
        body.reason,
    )
    notify_many(
        db,
        offer_crud.offer_owner_ids(db, offer),
        "offer_cancelled",
        f"Un administrateur a annulé votre offre « {offer.item_description} » : "
        f"{body.reason}",
        "/offers",
    )
    db.commit()
    db.refresh(offer)
    return _offer_out(offer)


# ── Transactions ──────────────────────────────────────────────────────────


def _transaction_out(tx: Transaction) -> AdminTransactionOut:
    offer = tx.offer
    seller = None
    if offer:
        seller = offer.user.username if offer.user else None
        if offer.faction_id is not None:
            seller = offer.faction.name if offer.faction else None
    buyer = tx.buyer_user.username if tx.buyer_user else None
    if tx.buyer_faction_id is not None:
        buyer = tx.buyer_faction.name if tx.buyer_faction else None
    return AdminTransactionOut(
        transaction_id=tx.transaction_id,
        offer_id=tx.offer_id,
        item_description=offer.item_description if offer else "",
        buyer_name=buyer,
        seller_name=seller,
        amount=float(tx.amount),
        currency_name=tx.currency_name,
        quantity=tx.quantity,
        timestamp=tx.timestamp,
        cancelled_at=tx.cancelled_at,
        cancelled_by_name=tx.cancelled_by_name,
        cancel_reason=tx.cancel_reason,
    )


@router.get("/transactions", response_model=list[AdminTransactionOut])
def list_all_transactions(
    state: str = Query("all", pattern="^(all|active|cancelled)$"),
    q: Optional[str] = Query(None, max_length=100, description="Words in the item"),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Every transaction, newest first."""
    query = db.query(Transaction).join(Offer, Transaction.offer_id == Offer.offer_id)
    if state == "active":
        query = query.filter(Transaction.cancelled_at.is_(None))
    elif state == "cancelled":
        query = query.filter(Transaction.cancelled_at.is_not(None))
    if q and q.strip():
        query = query.filter(
            Offer.item_description.ilike(f"%{_escape_like(q)}%", escape="\\")
        )
    rows = (
        query.order_by(Transaction.timestamp.desc(), Transaction.transaction_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_transaction_out(t) for t in rows]


@router.post(
    "/transactions/{transaction_id}/cancel", response_model=AdminTransactionCancelled
)
def cancel_transaction(
    transaction_id: int,
    body: AdminReason,
    db: Session = Depends(get_db),
    admin: User = Depends(_admin_only),
):
    """Cancel a transaction: the units go back on their offer.

    The row is kept, marked as cancelled. A closed offer is reopened. A
    transaction from before quantities were recorded can't give its units back:
    it is only marked.
    """
    tx = (
        db.query(Transaction)
        .filter(Transaction.transaction_id == transaction_id)
        .with_for_update()
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.cancelled_at is not None:
        raise HTTPException(
            status_code=409, detail="This transaction is already cancelled"
        )
    offer = (
        db.query(Offer).filter(Offer.offer_id == tx.offer_id).with_for_update().one()
    )

    restored = reopened = False
    if tx.quantity and offer.status in (OfferStatus.OPEN, OfferStatus.CLOSED):
        offer.quantity += tx.quantity
        offer.updated_at = utcnow()
        restored = True
        if offer.status == OfferStatus.CLOSED:
            offer.status = OfferStatus.OPEN
            offer.accepted_by_user_id = None
            offer.accepted_by_faction_id = None
            offer.expires_at = None  # it would be cancelled again at once
            reopened = True

    tx.cancelled_at = utcnow()
    tx.cancelled_by_name = admin.username[:50]
    tx.cancel_reason = body.reason

    create_offer_history(
        db,
        offer.offer_id,
        OfferAction.UPDATED,
        actor_user_id=admin.user_id,
        notes=(
            f"Transaction #{tx.transaction_id} cancelled by an administrator: "
            f"{body.reason}"
        )[:500],
        commit=False,
    )
    audit.record(
        db,
        admin,
        audit.AuditAction.TRANSACTION_CANCELLED,
        "transaction",
        tx.transaction_id,
        offer.item_description,
        body.reason,
    )

    buyers = (
        [tx.buyer_user_id]
        if tx.buyer_user_id is not None
        else members_with_permission(
            db, tx.buyer_faction_id, FactionPermission.ACCEPT_OFFERS
        )
    )
    notify_many(
        db,
        [*buyers, *offer_crud.offer_owner_ids(db, offer)],
        "transaction_cancelled",
        f"Un administrateur a annulé la transaction sur « "
        f"{offer.item_description} » : {body.reason}",
        "/transactions",
    )
    db.commit()
    db.refresh(tx)
    return AdminTransactionCancelled(
        transaction=_transaction_out(tx),
        quantity_restored=restored,
        offer_reopened=reopened,
    )


# ── Currencies ────────────────────────────────────────────────────────────

# A money admin runs every currency: these tools are theirs as well
_currency_staff = require_global_role(
    GlobalRoleName.ADMIN.value, GlobalRoleName.MONEY_ADMIN.value
)


def _currency_out(currency: Currency) -> AdminCurrencyOut:
    return AdminCurrencyOut(
        currency_id=currency.currency_id,
        name=currency.name,
        symbol=currency.symbol,
        factions=[
            CurrencyFactionOut(
                faction_id=link.faction_id,
                faction_name=link.faction.name if link.faction else None,
                is_issuer=link.is_issuer,
                joined_at=link.joined_at,
            )
            for link in currency.links
        ],
        total_in_circulation=currency.total_in_circulation,
        created_at=currency.created_at,
    )


@router.get("/currencies", response_model=list[AdminCurrencyOut])
def list_all_currencies(
    db: Session = Depends(get_db),
    _: User = Depends(_currency_staff),
):
    """Every faction's currency, with its declared total in circulation."""
    return [_currency_out(c) for c in db.query(Currency).order_by(Currency.name)]


def _recording(db: Session, action):
    """Run a currency change; its audit entry is only kept if it succeeds."""
    try:
        return action()
    except HTTPException:
        db.rollback()  # drops the pending audit entry too
        raise


@router.post(
    "/currencies",
    response_model=AdminCurrencyOut,
    status_code=status.HTTP_201_CREATED,
)
def create_currency(
    body: CurrencyCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(_currency_staff),
):
    """Create a currency for any faction."""
    faction = faction_crud.get_faction(db, body.faction_id)
    if not faction or faction.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Faction not found")
    audit.record(
        db,
        admin,
        audit.AuditAction.CURRENCY_CREATED,
        "currency",
        None,
        body.name,
        f"Pour {faction.name}",
    )
    currency = _recording(
        db,
        lambda: currency_crud.create_currency(db, body, actor_user_id=admin.user_id),
    )
    return _currency_out(currency)


@router.put("/currencies/{currency_id}", response_model=AdminCurrencyOut)
def update_currency(
    currency_id: int,
    body: CurrencyUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(_currency_staff),
):
    """Rename a currency, change its symbol or its declared total."""
    currency = currency_crud.get_currency(db, currency_id)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    changes = []
    if body.name is not None and body.name != currency.name:
        changes.append(f"nom → {body.name}")
    if body.symbol is not None and body.symbol != currency.symbol:
        changes.append(f"symbole → {body.symbol}")
    if (
        body.total_in_circulation is not None
        and body.total_in_circulation != currency.total_in_circulation
    ):
        changes.append(
            f"total {currency.total_in_circulation} → {body.total_in_circulation}"
        )
    audit.record(
        db,
        admin,
        audit.AuditAction.CURRENCY_CHANGED,
        "currency",
        currency.currency_id,
        currency.name,
        ", ".join(changes) or "aucun changement",
    )
    updated = _recording(
        db,
        lambda: currency_crud.update_currency(
            db, currency_id, body, actor_user_id=admin.user_id
        ),
    )
    return _currency_out(updated)


@router.delete("/currencies/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(_currency_staff),
):
    """Delete a currency nothing uses yet."""
    currency = currency_crud.get_currency(db, currency_id)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    audit.record(
        db,
        admin,
        audit.AuditAction.CURRENCY_DELETED,
        "currency",
        currency.currency_id,
        currency.name,
        None,
    )
    _recording(db, lambda: currency_crud.delete_currency(db, currency_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Read-only dumps, to debug ─────────────────────────────────────────────


def _offers_by_status(db: Session, **owner) -> dict[str, int]:
    counts = {s.value: 0 for s in OfferStatus}
    rows = (
        db.query(Offer.status, func.count(Offer.offer_id))
        .filter_by(**owner)
        .group_by(Offer.status)
    )
    for state, count in rows:
        counts[state.value] = count
    return counts


@router.get("/users/{user_id}/state", response_model=AdminUserState)
def user_state(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """What the server knows of an account (never the password hash)."""
    user = _target_user(db, user_id)
    pending = (
        db.query(Faction.name)
        .join(JoinRequest, JoinRequest.faction_id == Faction.faction_id)
        .filter(JoinRequest.user_id == user_id, JoinRequest.status == "PENDING")
        .first()
    )
    return AdminUserState(
        user=_user_out(
            user,
            {user.faction_id: user.faction.name if user.faction else None},
            {user.role_id: user.role.name if user.role else None},
        ),
        token_version=user.token_version or 0,
        offers_by_status=_offers_by_status(db, user_id=user_id),
        purchases=db.query(Transaction)
        .filter(Transaction.buyer_user_id == user_id)
        .count(),
        sales=db.query(Transaction)
        .join(Offer, Transaction.offer_id == Offer.offer_id)
        .filter(Offer.user_id == user_id)
        .count(),
        unread_notifications=db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count(),
        pending_join_request=pending[0] if pending else None,
        trains_owned=db.query(Train)
        .filter(Train.owner_user_id == user_id, Train.retired_at.is_(None))
        .count(),
    )


@router.get("/factions/{faction_id}/state", response_model=AdminFactionState)
def faction_state(
    faction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """What the server knows of a faction, archived ones included."""
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    members = db.query(User).filter(User.faction_id == faction_id).all()
    per_role: dict[int, int] = {}
    for m in members:
        per_role[m.role_id] = per_role.get(m.role_id, 0) + 1
    roles = db.query(Role).filter(Role.faction_id == faction_id).order_by(Role.name)
    leader = next(
        (m.username for m in members if m.role and m.role.name == LEADER_ROLE_NAME),
        None,
    )
    return AdminFactionState(
        faction=AdminFactionOut(
            faction_id=faction.faction_id,
            name=faction.name,
            is_approved=bool(faction.is_approved),
            requires_approval=faction.requires_approval,
            member_count=len(members),
            created_at=faction.created_at,
            deleted_at=faction.deleted_at,
        ),
        description=faction.description,
        leader=leader,
        roles=[
            AdminRoleState(name=r.name, member_count=per_role.get(r.role_id, 0))
            for r in roles
        ],
        currency=_currency_out(faction.currency) if faction.currency else None,
        offers_by_status=_offers_by_status(db, faction_id=faction_id),
        pending_join_requests=db.query(JoinRequest)
        .filter(JoinRequest.faction_id == faction_id, JoinRequest.status == "PENDING")
        .count(),
        trains_owned=db.query(Train)
        .filter(Train.owner_faction_id == faction_id, Train.retired_at.is_(None))
        .count(),
    )
