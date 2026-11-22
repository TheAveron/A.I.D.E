"""Offer expiry, and the admin tools for offers, transactions and currencies."""

from datetime import timedelta

import pytest
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import admin, admin_market, notifications, transactions
from app.database import AuditLog, Offer, Transaction, User
from app.database.clock import utcnow
from app.misc import OfferStatus


@pytest.fixture
def menv(env):  # noqa: F811
    """env + the admin and transaction routers + an admin ("root")."""
    for module in (admin, admin_market, transactions, notifications):
        env.client.app.include_router(module.router)
    s = env.Session()
    s.add(User(user_id=40, username="root", hashed_password=PW_HASH, is_admin=True))
    s.commit()
    s.close()
    return env


def _offer(env, who="alice", **extra):  # noqa: F811
    body = {
        "offer_type": "SELL",
        "item_description": "épée",
        "currency_name": "Diamant",
        "price_per_unit": 2,
        "quantity": 10,
        **extra,
    }
    if who == "alice":
        body["faction_id"] = 1
    else:
        body["user_id"] = 2
    r = env.client.post("/offers/create", json=body, headers=env.h(who))
    assert r.status_code == 201, r.text
    return r.json()["offer_id"]


def _accept(env, offer_id, quantity=None, who="newbie"):  # noqa: F811
    body = {"buyer_user_id": 2}
    if quantity:
        body["quantity"] = quantity
    r = env.client.post(f"/offers/accept/{offer_id}", json=body, headers=env.h(who))
    assert r.status_code == 202, r.text
    return r.json()["transaction_id"]


def _cancel_tx(env, tx_id, who="root", reason="erreur"):  # noqa: F811
    return env.client.post(
        f"/admin/transactions/{tx_id}/cancel",
        json={"reason": reason},
        headers=env.h(who),
    )


def _audit(env):  # noqa: F811
    s = env.Session()
    rows = [
        (a.actor_name, a.action, a.target_name, a.detail) for a in s.query(AuditLog)
    ]
    s.close()
    return rows


def _status(env, offer_id):  # noqa: F811
    s = env.Session()
    try:
        return s.get(Offer, offer_id).status
    finally:
        s.close()


# ── expiry ────────────────────────────────────────────────────────────────


def test_an_expiry_must_be_in_the_future_and_within_a_year(menv):
    soon = (utcnow() + timedelta(days=1)).isoformat() + "Z"
    assert _offer(menv, expires_at=soon)
    for bad in (
        (utcnow() - timedelta(minutes=1)).isoformat() + "Z",
        (utcnow() + timedelta(days=400)).isoformat() + "Z",
    ):
        r = menv.client.post(
            "/offers/create",
            json={
                "offer_type": "SELL",
                "item_description": "x",
                "currency_name": "Diamant",
                "price_per_unit": 1,
                "quantity": 1,
                "faction_id": 1,
                "expires_at": bad,
            },
            headers=menv.h("alice"),
        )
        assert r.status_code == 422


def test_the_expiry_is_returned_and_can_be_changed_or_cleared(menv):
    when = (utcnow() + timedelta(days=2)).replace(microsecond=0)
    oid = _offer(menv, expires_at=when.isoformat() + "Z")
    got = menv.client.get(f"/offers/detail/{oid}", headers=menv.h("alice")).json()
    assert got["expires_at"].startswith(when.isoformat())
    r = menv.client.put(
        f"/offers/update/{oid}", json={"expires_at": None}, headers=menv.h("alice")
    )
    assert r.status_code == 202
    assert r.json()["expires_at"] is None


def _make_overdue(env, offer_id):  # noqa: F811
    s = env.Session()
    s.get(Offer, offer_id).expires_at = utcnow() - timedelta(minutes=1)
    s.commit()
    s.close()


def test_an_overdue_offer_is_cancelled_when_listed_and_its_owner_told(menv):
    oid = _offer(menv, expires_at=(utcnow() + timedelta(hours=1)).isoformat() + "Z")
    keep = _offer(menv)
    _make_overdue(menv, oid)

    ids = [o["offer_id"] for o in menv.client.get("/offers/list?status=OPEN").json()]
    assert oid not in ids and keep in ids
    assert _status(menv, oid) == OfferStatus.CANCELLED
    history = menv.client.get(f"/history?offer_id={oid}", headers=menv.h("alice"))
    assert "expired" in str(history.json()).lower()


def test_nobody_can_accept_an_overdue_offer(menv):
    oid = _offer(menv, expires_at=(utcnow() + timedelta(hours=1)).isoformat() + "Z")
    _make_overdue(menv, oid)
    r = menv.client.post(
        f"/offers/accept/{oid}", json={"buyer_user_id": 2}, headers=menv.h("newbie")
    )
    assert r.status_code == 400
    assert _status(menv, oid) == OfferStatus.CANCELLED


# ── offers ────────────────────────────────────────────────────────────────


def test_only_admins_use_the_admin_market(menv):
    for url in ("/admin/offers", "/admin/transactions", "/admin/currencies"):
        assert menv.client.get(url, headers=menv.h("alice")).status_code == 403
        assert menv.client.get(url).status_code == 401
        assert menv.client.get(url, headers=menv.h("root")).status_code == 200


def test_an_admin_sees_private_offers_too(menv):
    _offer(menv, allowed_user_ids=[1])
    rows = menv.client.get("/admin/offers", headers=menv.h("root")).json()
    assert len(rows) == 1
    assert rows[0]["is_private"] is True
    assert (rows[0]["owner_kind"], rows[0]["owner_name"]) == ("faction", "Alpha")
    assert menv.client.get("/offers/list", headers=menv.h("newbie")).json() == []


def test_an_admin_cancels_any_open_offer_with_a_reason(menv):
    oid = _offer(menv)
    r = menv.client.post(
        f"/admin/offers/{oid}/cancel", json={"reason": " "}, headers=menv.h("root")
    )
    assert r.status_code == 422  # a reason is required
    r = menv.client.post(
        f"/admin/offers/{oid}/cancel",
        json={"reason": "arnaque"},
        headers=menv.h("root"),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"
    assert _status(menv, oid) == OfferStatus.CANCELLED
    assert ("root", "offer_cancelled", "épée", "arnaque") in _audit(menv)
    notes = menv.client.get("/notifications", headers=menv.h("alice")).json()
    assert "arnaque" in str(notes)
    # twice, unknown, and by somebody who is not an admin
    again = menv.client.post(
        f"/admin/offers/{oid}/cancel",
        json={"reason": "arnaque"},
        headers=menv.h("root"),
    )
    assert again.status_code == 409
    assert (
        menv.client.post(
            "/admin/offers/999/cancel",
            json={"reason": "arnaque"},
            headers=menv.h("root"),
        ).status_code
        == 404
    )
    other = _offer(menv)
    assert (
        menv.client.post(
            f"/admin/offers/{other}/cancel",
            json={"reason": "arnaque"},
            headers=menv.h("alice"),
        ).status_code
        == 403
    )


def test_offers_can_be_filtered_by_state_and_words(menv):
    a, b = _offer(menv), _offer(menv, item_description="pioche")
    menv.client.post(
        f"/admin/offers/{a}/cancel", json={"reason": "test"}, headers=menv.h("root")
    )
    get = lambda **p: [  # noqa: E731
        o["offer_id"]
        for o in menv.client.get(
            "/admin/offers", params=p, headers=menv.h("root")
        ).json()
    ]
    assert get(state="cancelled") == [a]
    assert get(state="open") == [b]
    assert get(q="pioch") == [b]
    assert (
        menv.client.get("/admin/offers?state=nope", headers=menv.h("root")).status_code
        == 422
    )


# ── transactions ──────────────────────────────────────────────────────────


def test_a_transaction_records_its_quantity(menv):
    oid = _offer(menv)
    tx = _accept(menv, oid, 4)
    s = menv.Session()
    assert s.get(Transaction, tx).quantity == 4
    s.close()
    rows = menv.client.get("/admin/transactions", headers=menv.h("root")).json()
    assert [(r["buyer_name"], r["seller_name"], r["quantity"]) for r in rows] == [
        ("newbie", "Alpha", 4)
    ]


def test_cancelling_a_transaction_gives_the_units_back(menv):
    oid = _offer(menv)
    tx = _accept(menv, oid, 4)
    r = _cancel_tx(menv, tx)
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["quantity_restored"], body["offer_reopened"]) == (True, False)
    assert body["transaction"]["cancelled_by_name"] == "root"
    assert body["transaction"]["cancel_reason"] == "erreur"
    s = menv.Session()
    assert s.get(Offer, oid).quantity == 10
    assert s.get(Transaction, tx).cancelled_at is not None  # the row is kept
    s.close()
    assert ("root", "transaction_cancelled", "épée", "erreur") in _audit(menv)
    for who in ("newbie", "alice"):
        notes = menv.client.get("/notifications", headers=menv.h(who)).json()
        assert "erreur" in str(notes)
    assert _cancel_tx(menv, tx).status_code == 409  # only once


def test_a_closed_offer_is_reopened(menv):
    oid = _offer(menv, who="newbie", quantity=3)
    tx = _accept(menv, oid, who="alice")  # alice buys it all as a user
    assert _status(menv, oid) == OfferStatus.CLOSED
    r = _cancel_tx(menv, tx)
    assert r.json()["offer_reopened"] is True
    s = menv.Session()
    offer = s.get(Offer, oid)
    assert (offer.status, offer.quantity, offer.accepted_by_user_id) == (
        OfferStatus.OPEN,
        3,
        None,
    )
    s.close()


def test_a_cancelled_offer_gets_no_units_back(menv):
    oid = _offer(menv)
    tx = _accept(menv, oid, 4)
    menv.client.post(
        f"/admin/offers/{oid}/cancel", json={"reason": "stop"}, headers=menv.h("root")
    )
    body = _cancel_tx(menv, tx).json()
    assert (body["quantity_restored"], body["offer_reopened"]) == (False, False)
    s = menv.Session()
    assert s.get(Offer, oid).quantity == 6
    s.close()


def test_an_old_transaction_without_quantity_is_only_marked(menv):
    oid = _offer(menv)
    tx = _accept(menv, oid, 4)
    s = menv.Session()
    s.get(Transaction, tx).quantity = None
    s.commit()
    s.close()
    body = _cancel_tx(menv, tx).json()
    assert body["quantity_restored"] is False
    s = menv.Session()
    assert s.get(Offer, oid).quantity == 6
    s.close()


def test_only_admins_cancel_transactions_and_states_filter(menv):
    oid = _offer(menv)
    one, two = _accept(menv, oid, 1), _accept(menv, oid, 1)
    assert _cancel_tx(menv, one, who="alice").status_code == 403
    assert _cancel_tx(menv, 999).status_code == 404
    _cancel_tx(menv, two)
    get = lambda state: [  # noqa: E731
        t["transaction_id"]
        for t in menv.client.get(
            "/admin/transactions", params={"state": state}, headers=menv.h("root")
        ).json()
    ]
    assert get("active") == [one]
    assert get("cancelled") == [two]
    assert sorted(get("all")) == [one, two]
    # the ordinary listing shows the cancellation too
    mine = menv.client.get("/transactions/", headers=menv.h("newbie")).json()
    assert {t["transaction_id"]: t["cancel_reason"] for t in mine}[two] == "erreur"


# ── currencies ────────────────────────────────────────────────────────────


def test_an_admin_manages_any_currency(menv):
    h = menv.h("root")
    c = menv.client
    assert [x["name"] for x in c.get("/admin/currencies", headers=h).json()] == [
        "Diamant"
    ]
    # a faction that does not exist, one that already has a currency
    assert (
        c.post("/admin/currencies", json={"name": "X", "faction_id": 99}, headers=h)
    ).status_code == 404
    assert (
        c.post("/admin/currencies", json={"name": "X", "faction_id": 1}, headers=h)
    ).status_code == 409
    assert _audit(menv) == []  # a refused change leaves no trace

    r = c.post("/admin/currencies", json={"name": "Or", "faction_id": 3}, headers=h)
    assert r.status_code == 201
    assert [(f["faction_name"], f["is_issuer"]) for f in r.json()["factions"]] == [
        ("Sans Faction", True)
    ]
    or_id = r.json()["currency_id"]

    r = c.put(
        f"/admin/currencies/{or_id}",
        json={"symbol": "$", "total_in_circulation": 50, "notes": "départ"},
        headers=h,
    )
    assert r.status_code == 200
    assert (r.json()["symbol"], r.json()["total_in_circulation"]) == ("$", 50)

    assert c.delete(f"/admin/currencies/{or_id}", headers=h).status_code == 204
    assert c.delete(f"/admin/currencies/{or_id}", headers=h).status_code == 404
    assert [a[1] for a in _audit(menv)] == [
        "currency_created",
        "currency_changed",
        "currency_deleted",
    ]


def test_a_used_currency_cannot_be_deleted_even_by_an_admin(menv):
    _offer(menv)
    r = menv.client.delete("/admin/currencies/1", headers=menv.h("root"))
    assert r.status_code == 409
    assert _audit(menv) == []


def test_currencies_are_for_admins_only(menv):
    for call in (
        lambda h: menv.client.post(
            "/admin/currencies", json={"name": "Or", "faction_id": 3}, headers=h
        ),
        lambda h: menv.client.put("/admin/currencies/1", json={}, headers=h),
        lambda h: menv.client.delete("/admin/currencies/1", headers=h),
    ):
        assert call(menv.h("alice")).status_code == 403


# ── dumps ─────────────────────────────────────────────────────────────────


def test_the_state_dumps(menv):
    oid = _offer(menv)
    _accept(menv, oid, 2)
    h = menv.h("root")
    u = menv.client.get("/admin/users/2/state", headers=h).json()
    assert u["user"]["username"] == "newbie"
    assert (u["purchases"], u["sales"], u["token_version"]) == (1, 0, 0)
    assert "hashed_password" not in str(u)
    f = menv.client.get("/admin/factions/1/state", headers=h).json()
    assert f["faction"]["name"] == "Alpha"
    assert f["leader"] == "alice"
    assert f["offers_by_status"]["OPEN"] == 1
    assert f["currency"]["name"] == "Diamant"
    assert menv.client.get("/admin/users/999/state", headers=h).status_code == 404
    assert menv.client.get("/admin/factions/999/state", headers=h).status_code == 404
    assert (
        menv.client.get("/admin/users/2/state", headers=menv.h("alice")).status_code
        == 403
    )
    assert (
        menv.client.get("/admin/factions/1/state", headers=menv.h("alice")).status_code
        == 403
    )
