"""GET /transactions: pagination on top of the visibility rules."""

from datetime import datetime, timedelta

import pytest
from test_hardening import env  # noqa: F401  (pytest fixture)

from app.api import transactions
from app.database import Offer, Transaction
from app.misc import OfferStatus, OfferType


@pytest.fixture
def many(env):  # noqa: F811
    env.client.app.include_router(transactions.router)
    s = env.Session()
    s.add(
        Offer(
            offer_id=1,
            offer_type=OfferType.SELL,
            item_description="x",
            currency_id=1,
            price_per_unit=1,
            quantity=1,
            init_quantity=1,
            status=OfferStatus.OPEN,
            user_id=1,
        )
    )
    s.commit()
    base = datetime(2026, 1, 1)
    s.add_all(
        Transaction(
            transaction_id=i,
            offer_id=1,
            buyer_user_id=2,
            amount=1,
            currency_id=1,
            timestamp=base + timedelta(minutes=i),
        )
        for i in range(1, 8)
    )
    s.commit()
    s.close()
    return env


def ids(response):
    return [t["transaction_id"] for t in response.json()]


def test_newest_first_and_a_page_at_a_time(many):
    h = many.h("alice")
    first = many.client.get("/transactions/?limit=3", headers=h)
    second = many.client.get("/transactions/?limit=3&skip=3", headers=h)
    last = many.client.get("/transactions/?limit=3&skip=6", headers=h)

    assert ids(first) == [7, 6, 5]
    assert ids(second) == [4, 3, 2]
    assert ids(last) == [1]


def test_everything_is_returned_by_default(many):
    r = many.client.get("/transactions/", headers=many.h("alice"))
    assert ids(r) == [7, 6, 5, 4, 3, 2, 1]


@pytest.mark.parametrize("query", ["limit=0", "limit=501", "skip=-1"])
def test_out_of_range_paging_is_a_422(many, query):
    r = many.client.get(f"/transactions/?{query}", headers=many.h("alice"))
    assert r.status_code == 422


def test_paging_does_not_widen_what_a_user_may_see(many):
    # "newbie" bought, so they see them; a stranger sees nothing, at any offset
    assert len(many.client.get("/transactions/", headers=many.h("newbie")).json()) == 7
    s = many.Session()
    from test_hardening import PW_HASH

    from app.database import User

    s.add(User(user_id=9, username="stranger", hashed_password=PW_HASH))
    s.commit()
    s.close()
    r = many.client.get("/transactions/?limit=500", headers=many.h("stranger"))
    assert r.json() == []
