"""Basic persistence and relationship checks on the ORM models."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import Currency, Faction, Offer, User
from app.misc import OfferStatus, OfferType


def test_create_user(session):
    user = User(username="test_user", hashed_password="x", email="user@example.com")
    session.add(user)
    session.commit()
    result = session.query(User).filter_by(username="test_user").first()
    assert result.email == "user@example.com"
    assert result.is_admin is False


def test_usernames_are_unique(session):
    session.add(User(username="dup", hashed_password="x"))
    session.commit()
    session.add(User(username="dup", hashed_password="y"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_create_faction_and_link_user(session):
    faction = Faction(name="Alpha", description="Test faction")
    user = User(username="member1", hashed_password="x", faction=faction)

    session.add_all([faction, user])
    session.commit()

    result = session.query(User).filter_by(username="member1").first()
    assert result.faction.name == "Alpha"
    assert [u.username for u in faction.users] == ["member1"]


def test_currency_belongs_to_a_faction(session):
    faction = Faction(name="Alpha")
    session.add(faction)
    session.commit()

    session.add(Currency(name="Diamant", faction_id=faction.faction_id))
    session.commit()

    result = session.query(Currency).first()
    assert result.name == "Diamant"
    assert result.faction_id == faction.faction_id


def _offer(**over) -> Offer:
    data = dict(
        offer_type=OfferType.SELL,
        item_description="Laser Gun",
        currency_name="Gold",
        price_per_unit=500.0,
        quantity=1,
        init_quantity=1,
        status=OfferStatus.OPEN,
    )
    data.update(over)
    return Offer(**data)


def test_offer_creation_and_user_relationships(session):
    creator = User(username="creator", hashed_password="x")
    accepter = User(username="accepter", hashed_password="x")
    session.add_all([creator, accepter, Currency(name="Gold")])
    session.commit()

    session.add(_offer(user_id=creator.user_id, accepted_by_user_id=accepter.user_id))
    session.commit()

    result = session.query(Offer).first()
    assert result.user.username == "creator"
    assert result.accepted_by_user_obj.username == "accepter"
    assert result.item_description == "Laser Gun"
    assert result.currency_name == "Gold"


def test_an_offer_needs_exactly_one_owner(session):
    session.add(Currency(name="Gold"))
    session.commit()
    session.add(_offer())  # neither user nor faction
    with pytest.raises(IntegrityError):
        session.commit()
