from sqlalchemy.orm import Session

from ..database import Faction, Offer, OfferStatus, Transaction, User


def fulfill_offer(
    db: Session, offer: Offer, buyer: User, buyer_faction: Faction | None = None
) -> Transaction:
    offer.status = OfferStatus.CLOSED  # type: ignore
    db.add(offer)

    transaction = Transaction(
        offer_id=offer.id,
        buyer_id=buyer.id if buyer else None,
        buyer_faction_id=buyer_faction.id if buyer_faction else None,
        amount=offer.price,
        currency=offer.currency,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
