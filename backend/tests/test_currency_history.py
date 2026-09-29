import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import (Base, Currency, CurrencyHistory, Faction, Role, User)
from app.database.models import (currency, currency_history, faction,
                                 faction_role, user)
from app.crud import currencies as crud
from app.crud import currency_history as crud_hist
from app.schemas import CurrencyCreate, CurrencyUpdate
from app.api import currencies as api

TABLES = [Faction.__table__, Role.__table__, User.__table__,
          Currency.__table__, CurrencyHistory.__table__]


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=TABLES)
    s = sessionmaker(bind=engine)()
    s.add_all([Faction(faction_id=1, name="A"), Faction(faction_id=2, name="B")])
    s.add(Role(role_id=1, name="Tresorier", faction_id=1, manage_funds=True))
    s.add(Role(role_id=2, name="Membre", faction_id=1))
    s.add(User(user_id=1, username="treasurer", hashed_password="x", faction_id=1, role_id=1))
    s.add(User(user_id=2, username="member", hashed_password="x", faction_id=1, role_id=2))
    s.add(User(user_id=3, username="other", hashed_password="x", faction_id=2))
    s.commit()
    yield s
    s.close()


def hist(db, name="Diamant"):
    return crud_hist.get_currency_histories(db, name)


def test_creation_logs_initial_value(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=100), actor_user_id=1)
    h = hist(db)
    assert len(h) == 1
    assert (h[0].old_total_in_circulation, h[0].new_total_in_circulation) == (0, 100)
    assert h[0].actor_user_id == 1 and "Initial" in h[0].notes


def test_creation_with_zero_logs_nothing(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=0), actor_user_id=1)
    assert hist(db) == []


def test_update_logs_change_with_actor(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=100), actor_user_id=1)
    crud.update_currency(db, "Diamant", CurrencyUpdate(total_in_circulation=250), actor_user_id=1)
    h = hist(db)
    assert len(h) == 2
    latest = h[0]
    assert (latest.old_total_in_circulation, latest.new_total_in_circulation) == (100, 250)
    assert latest.actor_user_id == 1
    assert db.get(Currency, "Diamant").total_in_circulation == 250


def test_same_value_or_symbol_only_update_not_logged(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=100), actor_user_id=1)
    crud.update_currency(db, "Diamant", CurrencyUpdate(total_in_circulation=100), actor_user_id=1)
    crud.update_currency(db, "Diamant", CurrencyUpdate(symbol="D"), actor_user_id=1)
    assert len(hist(db)) == 1
    assert db.get(Currency, "Diamant").symbol == "D"


def test_history_scoped_per_currency_and_newest_first(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=1), actor_user_id=1)
    crud.create_currency(db, CurrencyCreate(name="Emeraude", faction_id=2, total_in_circulation=5), actor_user_id=3)
    for v in (2, 3, 4):
        crud.update_currency(db, "Diamant", CurrencyUpdate(total_in_circulation=v), actor_user_id=1)
    d = hist(db, "Diamant")
    assert [x.new_total_in_circulation for x in d] == [4, 3, 2, 1]
    assert len(hist(db, "Emeraude")) == 1


def test_delete_currency_removes_history(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=1), actor_user_id=1)
    crud.update_currency(db, "Diamant", CurrencyUpdate(total_in_circulation=9), actor_user_id=1)
    crud.delete_currency(db, "Diamant")
    assert db.query(CurrencyHistory).count() == 0


# ---- couche API : contrôle d'accès ----
def test_api_history_allowed_for_treasurer(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=1), actor_user_id=1)
    treasurer = db.get(User, 1)
    out = api.get_currency_history("Diamant", db=db, current_user=treasurer)
    assert len(out) == 1


def test_api_history_denied_without_manage_funds(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=1), actor_user_id=1)
    with pytest.raises(HTTPException) as e:
        api.get_currency_history("Diamant", db=db, current_user=db.get(User, 2))
    assert e.value.status_code == 403


def test_api_history_denied_for_other_faction(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=1), actor_user_id=1)
    other = db.get(User, 3)
    other.role = Role(role_id=9, name="T2", faction_id=2, manage_funds=True)
    db.commit()
    with pytest.raises(HTTPException) as e:
        api.get_currency_history("Diamant", db=db, current_user=other)
    assert e.value.status_code == 403


def test_api_history_404_unknown_currency(db):
    with pytest.raises(HTTPException) as e:
        api.get_currency_history("Nope", db=db, current_user=db.get(User, 1))
    assert e.value.status_code == 404


def test_api_update_records_authenticated_actor(db):
    crud.create_currency(db, CurrencyCreate(name="Diamant", faction_id=1, total_in_circulation=1), actor_user_id=1)
    api.update_currency("Diamant", CurrencyUpdate(total_in_circulation=7), db=db, current_user=db.get(User, 1))
    assert hist(db)[0].actor_user_id == 1
