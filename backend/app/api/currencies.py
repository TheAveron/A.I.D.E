"""Currencies, shared between factions.

A currency is used by one or more factions; the issuers among them run it.
Changing a currency (its name, symbol, total, factions, issuers) takes
`manage_funds` in an issuer faction, or the money admin role, which works on
every currency and leaves an entry in the audit trail when it is what lets the
caller through.

A faction starts using a currency through a link request: either it asks
(an issuer accepts) or an issuer proposes (the faction accepts).
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import audit
from ..crud import currencies as crud
from ..crud import currency_history as crud_currency_history
from ..crud import faction as crud_faction
from ..crud.notification import members_with_permission, notify_many
from ..database import Currency, CurrencyLinkRequest, Faction, User, get_db
from ..database.clock import utcnow
from ..misc import (CurrencyLinkKind, FactionPermission, JoinRequestStatus,
                    check_faction_permission)
from ..schemas import (CurrencyCreate, CurrencyFactionOut, CurrencyHistoryOut,
                       CurrencyInvite, CurrencyLinkRequestOut, CurrencyOut,
                       CurrencyPublic, CurrencyUpdate)

router = APIRouter(prefix="/currencies", tags=["Currencies"])

PENDING = JoinRequestStatus.PENDING.value


# ── Helpers ───────────────────────────────────────────────────────────────


def _factions_out(currency: Currency) -> list[CurrencyFactionOut]:
    return [
        CurrencyFactionOut(
            faction_id=link.faction_id,
            faction_name=link.faction.name if link.faction else None,
            is_issuer=link.is_issuer,
            joined_at=link.joined_at,
        )
        for link in currency.links
    ]


def _public(currency: Currency, viewer: User) -> CurrencyPublic:
    return CurrencyPublic(
        currency_id=currency.currency_id,
        name=currency.name,
        symbol=currency.symbol,
        factions=_factions_out(currency),
        can_manage=crud.can_manage(viewer, currency),
    )


def _full(currency: Currency, viewer: User) -> CurrencyOut:
    return CurrencyOut(
        **_public(currency, viewer).model_dump(),
        total_in_circulation=currency.total_in_circulation,
        created_at=currency.created_at,
        updated_at=currency.updated_at,
    )


def _currency_or_404(db: Session, currency_id: int) -> Currency:
    currency = crud.get_currency(db, currency_id)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Currency not found"
        )
    return currency


def _live_faction(db: Session, faction_id: int) -> Faction:
    faction = crud_faction.get_faction(db, faction_id)
    if not faction or faction.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Faction not found")
    return faction


def _require_details(user: User, currency: Currency) -> None:
    if not crud.can_view_details(user, currency):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the managers of a faction using this currency may see it",
        )


def _audit(
    db: Session,
    as_admin: bool,
    actor: User,
    action: audit.AuditAction,
    currency: Currency,
    detail: Optional[str],
) -> None:
    """Record a money admin's override (a manager's own action is not one)."""
    if as_admin:
        audit.record(
            db, actor, action, "currency", currency.currency_id, currency.name, detail
        )


def _notify_issuers(db: Session, currency: Currency, message: str) -> None:
    for faction_id in currency.issuer_faction_ids:
        _notify_faction(db, faction_id, message)


def _notify_faction(db: Session, faction_id: int, message: str) -> None:
    notify_many(
        db,
        members_with_permission(db, faction_id, FactionPermission.MANAGE_FUNDS),
        "currency",
        message,
        f"/faction/{faction_id}",
    )


def _flush(db: Session) -> None:
    """Write the pending changes now: a clash with the unique faction or the
    one-pending-request index (another request won a race, or the session
    autoflushes later) becomes a clean 409 rather than a 500."""
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This faction already uses a currency or has a pending request",
        )


# ── Reading ───────────────────────────────────────────────────────────────


@router.get("", response_model=list[CurrencyPublic])
def list_currencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Every currency (name, symbol, factions), to pick one to ask for."""
    return [_public(c, current_user) for c in crud.get_currencies(db, limit=500)]


@router.post("/create", response_model=CurrencyOut, status_code=status.HTTP_201_CREATED)
def create_currency(
    currency_in: CurrencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A new currency, issued by the faction that creates it."""
    as_admin = False
    if not crud.holds_manage_funds(current_user, currency_in.faction_id):
        if not crud.is_money_admin(current_user):
            check_faction_permission(
                current_user,
                FactionPermission.MANAGE_FUNDS,
                target_faction_id=currency_in.faction_id,
            )
        as_admin = True
    faction = _live_faction(db, currency_in.faction_id)
    if as_admin:
        audit.record(
            db,
            current_user,
            audit.AuditAction.CURRENCY_CREATED,
            "currency",
            None,
            currency_in.name,
            f"Pour {faction.name}",
        )
    # Duplicate name / second currency for the same faction -> 409 (raised by
    # the crud layer, which also covers the race between two requests).
    try:
        currency = crud.create_currency(
            db, currency_in, actor_user_id=current_user.user_id
        )
    except HTTPException:
        db.rollback()  # drops the pending audit entry too
        raise
    return _full(currency, current_user)


@router.get(
    "/faction/{faction_id}",
    response_model=CurrencyOut | CurrencyPublic | None,
    status_code=status.HTTP_200_OK,
)
def get_currency_by_faction(
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The currency a faction uses.

    Anyone logged in sees its name, symbol and factions (the faction list
    needs them); the declared total in circulation is for the members of the
    factions using it, and for money admins.
    """
    currency = crud.get_currency_by_faction(db, faction_id)
    if not currency:
        return None

    if current_user.faction_id in currency.faction_ids or crud.is_money_admin(
        current_user
    ):
        return _full(currency, current_user)
    return _public(currency, current_user)


@router.get("/detail/{currency_id}", response_model=CurrencyOut)
def get_currency_detail(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    currency = _currency_or_404(db, currency_id)
    _require_details(current_user, currency)
    return _full(currency, current_user)


@router.get("/history/{currency_id}", response_model=list[CurrencyHistoryOut])
def get_currency_history(
    currency_id: int,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Audit trail of the currency's declared total (and of its renames).

    For the holders of manage_funds in a faction using the currency, and for
    money admins.
    """
    currency = _currency_or_404(db, currency_id)
    _require_details(current_user, currency)
    return crud_currency_history.get_currency_histories(
        db, currency_id, skip=skip, limit=limit
    )


# ── Changing a currency ───────────────────────────────────────────────────


@router.put(
    "/update/{currency_id}",
    response_model=CurrencyOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def update_currency(
    currency_id: int,
    currency_in: CurrencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rename the currency, change its symbol or its declared total."""
    currency = _currency_or_404(db, currency_id)
    as_admin = crud.require_manager(current_user, currency)
    if as_admin:
        changes = []
        if currency_in.name is not None and currency_in.name != currency.name:
            changes.append(f"nom → {currency_in.name}")
        if currency_in.symbol is not None and currency_in.symbol != currency.symbol:
            changes.append(f"symbole → {currency_in.symbol}")
        if (
            currency_in.total_in_circulation is not None
            and currency_in.total_in_circulation != currency.total_in_circulation
        ):
            changes.append(
                f"total {currency.total_in_circulation} → "
                f"{currency_in.total_in_circulation}"
            )
        _audit(
            db,
            True,
            current_user,
            audit.AuditAction.CURRENCY_CHANGED,
            currency,
            ", ".join(changes) or "aucun changement",
        )
    try:
        updated = crud.update_currency(
            db, currency_id, currency_in, actor_user_id=current_user.user_id
        )
    except HTTPException:
        db.rollback()  # drops the pending audit entry too
        raise
    return _full(updated, current_user)


@router.delete("/delete/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a currency nothing (offers, transactions) refers to."""
    currency = _currency_or_404(db, currency_id)
    as_admin = crud.require_manager(current_user, currency)
    _audit(
        db,
        as_admin,
        current_user,
        audit.AuditAction.CURRENCY_DELETED,
        currency,
        None,
    )
    try:
        crud.delete_currency(db, currency_id)
    except HTTPException:
        db.rollback()
        raise
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{currency_id}/factions/{faction_id}/issuer", response_model=CurrencyOut)
def make_issuer(
    currency_id: int,
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Make a faction that uses the currency one of its issuers."""
    return _set_issuer(db, current_user, currency_id, faction_id, True)


@router.delete(
    "/{currency_id}/factions/{faction_id}/issuer", response_model=CurrencyOut
)
def unmake_issuer(
    currency_id: int,
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A faction stops being an issuer (the currency keeps at least one)."""
    return _set_issuer(db, current_user, currency_id, faction_id, False)


def _set_issuer(
    db: Session, user: User, currency_id: int, faction_id: int, is_issuer: bool
) -> CurrencyOut:
    currency = _currency_or_404(db, currency_id)
    as_admin = crud.require_manager(user, currency)
    link = crud.set_issuer(db, currency, faction_id, is_issuer)
    name = link.faction.name if link.faction else f"#{faction_id}"
    _audit(
        db,
        as_admin,
        user,
        audit.AuditAction.CURRENCY_ISSUER_CHANGED,
        currency,
        f"{name} {'devient' if is_issuer else 'n’est plus'} émettrice",
    )
    db.commit()
    db.refresh(currency)
    return _full(currency, user)


@router.delete("/{currency_id}/factions/{faction_id}", response_model=CurrencyOut)
def remove_faction(
    currency_id: int,
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A faction stops using the currency.

    The currency's managers may remove any faction; a faction's own holders
    of manage_funds may have it leave. The last issuer can't go.
    """
    currency = _currency_or_404(db, currency_id)
    leaving = crud.holds_manage_funds(current_user, faction_id)
    as_admin = False if leaving else crud.require_manager(current_user, currency)
    link = crud.get_link(db, currency_id, faction_id)
    name = link.faction.name if link and link.faction else f"#{faction_id}"
    crud.remove_faction(db, currency, faction_id)
    _audit(
        db,
        as_admin,
        current_user,
        audit.AuditAction.CURRENCY_FACTION_REMOVED,
        currency,
        f"{name} n’utilise plus la monnaie",
    )
    if leaving:
        _notify_issuers(
            db, currency, f"{name} n’utilise plus la monnaie {currency.name}"
        )
    else:
        _notify_faction(
            db, faction_id, f"Votre faction n’utilise plus la monnaie {currency.name}"
        )
    db.commit()
    db.refresh(currency)
    return _full(currency, current_user)


# ── Link requests: a faction asks, or an issuer proposes ──────────────────


def _pending(db: Session, request_id: int) -> CurrencyLinkRequest:
    request = (
        db.query(CurrencyLinkRequest)
        .filter(CurrencyLinkRequest.request_id == request_id)
        .first()
    )
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This request has already been dealt with",
        )
    return request


def _close(request: CurrencyLinkRequest, new_status: JoinRequestStatus, by: User):
    request.status = new_status.value
    request.decided_at = utcnow()
    request.decided_by_user_id = by.user_id


def _check_free(db: Session, currency: Currency, faction_id: int) -> None:
    """The faction may start using `currency`: it uses no currency yet."""
    current = crud.get_currency_by_faction(db, faction_id)
    if current is not None:
        detail = (
            "This faction already uses this currency"
            if current.currency_id == currency.currency_id
            else "This faction already uses another currency: it must leave it first"
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


@router.get("/links/faction/{faction_id}", response_model=list[CurrencyLinkRequestOut])
def faction_link_requests(
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A faction's pending requests and the invitations it received (for its
    holders of manage_funds)."""
    check_faction_permission(
        current_user, FactionPermission.MANAGE_FUNDS, target_faction_id=faction_id
    )
    return (
        db.query(CurrencyLinkRequest)
        .filter(
            CurrencyLinkRequest.faction_id == faction_id,
            CurrencyLinkRequest.status == PENDING,
        )
        .order_by(CurrencyLinkRequest.created_at, CurrencyLinkRequest.request_id)
        .all()
    )


@router.post("/links/{request_id}/accept", response_model=CurrencyLinkRequestOut)
def accept_link_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The receiving side accepts: the faction starts using the currency.

    A faction's request is accepted by the currency's managers; an invitation
    by the invited faction's holders of manage_funds (nobody may sign a
    faction up for a currency on its behalf, not even a money admin).
    """
    request = _pending(db, request_id)
    currency = request.currency
    as_admin = False
    if request.kind == CurrencyLinkKind.REQUEST.value:
        as_admin = crud.require_manager(current_user, currency)
    else:
        check_faction_permission(
            current_user,
            FactionPermission.MANAGE_FUNDS,
            target_faction_id=request.faction_id,
        )
    _check_free(db, currency, request.faction_id)
    crud.add_faction(db, currency, request.faction_id)
    _close(request, JoinRequestStatus.ACCEPTED, current_user)
    _flush(db)
    _audit(
        db,
        as_admin,
        current_user,
        audit.AuditAction.CURRENCY_FACTION_ADDED,
        currency,
        f"{request.faction.name} utilise la monnaie",
    )
    if request.kind == CurrencyLinkKind.REQUEST.value:
        _notify_faction(
            db,
            request.faction_id,
            f"Votre faction utilise désormais la monnaie {currency.name}",
        )
    else:
        _notify_issuers(
            db, currency, f"{request.faction.name} a accepté la monnaie {currency.name}"
        )
    db.commit()
    db.refresh(request)
    return request


@router.post("/links/{request_id}/refuse", response_model=CurrencyLinkRequestOut)
def refuse_link_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The receiving side says no."""
    request = _pending(db, request_id)
    currency = request.currency
    if request.kind == CurrencyLinkKind.REQUEST.value:
        crud.require_manager(current_user, currency)
        _notify_faction(
            db,
            request.faction_id,
            f"La demande pour utiliser la monnaie {currency.name} a été refusée",
        )
    else:
        check_faction_permission(
            current_user,
            FactionPermission.MANAGE_FUNDS,
            target_faction_id=request.faction_id,
        )
        _notify_issuers(
            db, currency, f"{request.faction.name} a refusé la monnaie {currency.name}"
        )
    _close(request, JoinRequestStatus.REFUSED, current_user)
    db.commit()
    db.refresh(request)
    return request


@router.delete("/links/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_link_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The side that asked withdraws its request or invitation."""
    request = _pending(db, request_id)
    if request.kind == CurrencyLinkKind.REQUEST.value:
        check_faction_permission(
            current_user,
            FactionPermission.MANAGE_FUNDS,
            target_faction_id=request.faction_id,
        )
    else:
        crud.require_manager(current_user, request.currency)
    _close(request, JoinRequestStatus.CANCELLED, current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{currency_id}/links", response_model=list[CurrencyLinkRequestOut])
def currency_link_requests(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The pending requests and invitations of a currency (for its managers)."""
    currency = _currency_or_404(db, currency_id)
    crud.require_manager(current_user, currency)
    return (
        db.query(CurrencyLinkRequest)
        .filter(
            CurrencyLinkRequest.currency_id == currency_id,
            CurrencyLinkRequest.status == PENDING,
        )
        .order_by(CurrencyLinkRequest.created_at, CurrencyLinkRequest.request_id)
        .all()
    )


@router.post(
    "/{currency_id}/links/request",
    response_model=CurrencyLinkRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def request_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The caller's faction asks to use the currency (manage_funds there)."""
    currency = _currency_or_404(db, currency_id)
    check_faction_permission(current_user, FactionPermission.MANAGE_FUNDS)
    faction = _live_faction(db, current_user.faction_id)
    _check_free(db, currency, faction.faction_id)
    request = CurrencyLinkRequest(
        currency_id=currency.currency_id,
        faction_id=faction.faction_id,
        kind=CurrencyLinkKind.REQUEST.value,
        status=PENDING,
        created_by_user_id=current_user.user_id,
    )
    db.add(request)
    _flush(db)
    _notify_issuers(
        db, currency, f"{faction.name} demande à utiliser la monnaie {currency.name}"
    )
    db.commit()
    db.refresh(request)
    return request


@router.post(
    "/{currency_id}/links/invite",
    response_model=CurrencyLinkRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def invite_faction(
    currency_id: int,
    body: CurrencyInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A manager of the currency proposes it to a faction, which accepts."""
    currency = _currency_or_404(db, currency_id)
    as_admin = crud.require_manager(current_user, currency)
    faction = _live_faction(db, body.faction_id)
    _check_free(db, currency, faction.faction_id)
    request = CurrencyLinkRequest(
        currency_id=currency.currency_id,
        faction_id=faction.faction_id,
        kind=CurrencyLinkKind.INVITATION.value,
        status=PENDING,
        created_by_user_id=current_user.user_id,
    )
    db.add(request)
    _flush(db)
    _audit(
        db,
        as_admin,
        current_user,
        audit.AuditAction.CURRENCY_FACTION_ADDED,
        currency,
        f"Proposée à {faction.name}",
    )
    _notify_faction(
        db,
        faction.faction_id,
        f"La monnaie {currency.name} est proposée à votre faction",
    )
    db.commit()
    db.refresh(request)
    return request
