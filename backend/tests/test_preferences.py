"""Account preferences: the theme, and which notifications arrive."""

import pytest
from test_hardening import env  # noqa: F401  (pytest fixture)

from app.api import join_requests, notifications, preferences
from app.database import Notification, UserPreferences


@pytest.fixture
def penv(env):  # noqa: F811
    for module in (preferences, notifications, join_requests):
        env.client.app.include_router(module.router)
    return env


def _notes(env, who):  # noqa: F811
    return [
        n["kind"] for n in env.client.get("/notifications", headers=env.h(who)).json()
    ]


def test_the_defaults_when_nothing_was_saved(penv):
    r = penv.client.get("/preferences", headers=penv.h("alice"))
    assert r.status_code == 200
    assert r.json() == {
        "theme": "dark",
        "notify_market": True,
        "notify_faction": True,
    }
    s = penv.Session()
    assert s.query(UserPreferences).count() == 0  # reading creates nothing
    s.close()


def test_preferences_need_a_login(penv):
    assert penv.client.get("/preferences").status_code == 401
    assert penv.client.put("/preferences", json={"theme": "dark"}).status_code == 401


def test_a_change_only_touches_what_was_sent(penv):
    h = penv.h("alice")
    r = penv.client.put("/preferences", json={"theme": "light"}, headers=h)
    assert r.status_code == 200
    assert r.json() == {"theme": "light", "notify_market": True, "notify_faction": True}
    r = penv.client.put("/preferences", json={"notify_market": False}, headers=h)
    assert r.json() == {
        "theme": "light",
        "notify_market": False,
        "notify_faction": True,
    }
    assert penv.client.get("/preferences", headers=h).json()["theme"] == "light"
    # somebody else's are their own
    other = penv.client.get("/preferences", headers=penv.h("newbie")).json()
    assert other == {"theme": "dark", "notify_market": True, "notify_faction": True}


@pytest.mark.parametrize(
    "body",
    [
        {"theme": "purple"},
        {"theme": None},
        {"notify_market": None},
        {"notify_faction": "maybe"},
    ],
)
def test_bad_values_are_refused(penv, body):
    r = penv.client.put("/preferences", json=body, headers=penv.h("alice"))
    assert r.status_code == 422


def test_switched_off_notifications_do_not_arrive(penv):
    from app.crud.notification import notify

    penv.client.put(
        "/preferences", json={"notify_market": False}, headers=penv.h("alice")
    )
    s = penv.Session()
    notify(s, 1, "offer_accepted", "bought")  # market: off
    notify(s, 1, "role_changed", "promoted")  # faction: still on
    notify(s, 2, "offer_accepted", "bought")  # somebody who kept the default
    s.commit()
    s.close()
    assert _notes(penv, "alice") == ["role_changed"]
    assert _notes(penv, "newbie") == ["offer_accepted"]


def test_security_and_moderation_notices_always_arrive(penv):
    from app.crud.notification import notify

    penv.client.put(
        "/preferences",
        json={"notify_market": False, "notify_faction": False},
        headers=penv.h("alice"),
    )
    s = penv.Session()
    for kind in (
        "password_reset",
        "kicked",
        "faction_deleted",
        "offer_cancelled",
        "transaction_cancelled",
        "offer_accepted",
        "join_request",
    ):
        notify(s, 1, kind, "x")
    s.commit()
    assert s.query(Notification).count() == 5  # the two optional ones are gone
    s.close()


def test_switching_a_category_back_on_restores_it(penv):
    from app.crud.notification import notify

    h = penv.h("alice")
    penv.client.put("/preferences", json={"notify_faction": False}, headers=h)
    penv.client.put("/preferences", json={"notify_faction": True}, headers=h)
    s = penv.Session()
    notify(s, 1, "join_request", "someone wants in")
    s.commit()
    s.close()
    assert _notes(penv, "alice") == ["join_request"]
