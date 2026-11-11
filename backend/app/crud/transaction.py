from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import Offer, Transaction, User
from ..misc import OfferAction, OfferStatus
from ..schemas import TransactionCreate
from .offer_history import create_offer_history


def create_transaction(
    db: Session, transaction_in: TransactionCreate, actor_user_id: int
) -> Transaction:
    offer = db.query(Offer).filter(Offer.offer_id == transaction_in.offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if not offer.is_open():
        raise HTTPException(
            status_code=400, detail="Offer is not open for transactions"
        )

    transaction = Transaction(**transaction_in.dict(), timestamp=datetime.utcnow())
    db.add(transaction)

    offer.status = OfferStatus.CLOSED
    offer.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(transaction)

    create_offer_history(
        db=db,
        offer_id=offer.offer_id,
        actor_user_id=actor_user_id,
        actor_faction_id=None,
        action=OfferAction.ACCEPTED,
        notes=f"Transaction {transaction.transaction_id} created",
    )

    return transaction


def get_transaction(db: Session, transaction_id: int) -> Transaction:
    tx = (
        db.query(Transaction)
        .filter(Transaction.transaction_id == transaction_id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


def get_transactions(
    db: Session,
    viewer: User,
    faction_id: Optional[int] = None,
    user_id: Optional[int] = None,
    offer_id: Optional[int] = None,
) -> list[Transaction]:
    """Transactions the viewer is allowed to see, newest first.

    Visible: those where the viewer bought, or sold through an offer they
    created, plus - for members whose role has `view_transactions` - those
    involving their faction. The optional filters match either side of the
    trade (buyer or offer creator) and only narrow that scope.
    """
    query = db.query(Transaction).join(
        Offer, Transaction.offer_id == Offer.offer_id
    )

    scope = [
        Transaction.buyer_user_id == viewer.user_id,
        Offer.user_id == viewer.user_id,
    ]
    if viewer.faction_id and viewer.role and viewer.role.view_transactions:
        scope += [
            Transaction.buyer_faction_id == viewer.faction_id,
            Offer.faction_id == viewer.faction_id,
        ]
    query = query.filter(or_(*scope))

    if faction_id is not None:
        query = query.filter(
            or_(
                Transaction.buyer_faction_id == faction_id,
                Offer.faction_id == faction_id,
            )
        )
    if user_id is not None:
        query = query.filter(
            or_(Transaction.buyer_user_id == user_id, Offer.user_id == user_id)
        )
    if offer_id is not None:
        query = query.filter(Transaction.offer_id == offer_id)

    return query.order_by(
        Transaction.timestamp.desc(), Transaction.transaction_id.desc()
    ).all()
