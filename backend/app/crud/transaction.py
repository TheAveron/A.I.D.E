from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..database import Offer, Transaction
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

    # Close offer automatically after transaction
    offer.status = OfferStatus.CLOSED
    offer.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(transaction)

    # Log acceptance in history
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
    db: Session, faction_id: Optional[int] = None, user_id: Optional[int] = None
) -> list[Transaction]:
    query = db.query(Transaction)

    if faction_id is not None:
        query = query.filter(Transaction.buyer_faction_id == faction_id)
    if user_id is not None:
        query = query.filter(Transaction.buyer_user_id == user_id)

    transactions = query.all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")

    return transactions
