"""Notifications: who gets told what, and that nobody reads the others'."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import join_requests, notifications
from app.database import Faction, Notification, Role, User


def _mount(env):  # noqa: F811
    env.client.app.include_router(join_requests.router)
    env.client.app.include_router(notifications.router)


def _mine(env, who, **params):  # noqa: F811
    r = env.client.get("/notifications", params=params, headers=env.h(who))
    assert r.status_code == 200, r.text
    return r.json()


def _kinds(env, who):  # noqa: F811
    return [n["kind"] for n in _mine(env, who)]


def _members(env):  # noqa: F811
    s = env.Session()
    s.add_all(
        [
            Role(role_id=30, name="Chef Adjoint", faction_id=1, handle_members=True),
            Role(role_id=31, name="Recrue", faction_id=1),
            Role(role_id=32, name="Invité", faction_id=1),
        ]
    )
    s.commit()
    s.add_all(
        [
            User(
                user_id=10,
                username="adele",
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=30,
            ),
            User(
                user_id=11,
                username="rory",
                hashed_password=PW_HASH,
                faction_id=1,
                role_id=31,
            ),
        ]
    )
    s.commit()
    s.close()


def test_a_new_user_has_none(env):  # noqa: F811
    _mount(env)
    assert _mine(env, "alice") == []
    r = env.client.get("/notifications/unread_count", headers=env.h("alice"))
    assert r.json() == {"count": 0}


def test_it_needs_a_login(env):  # noqa: F811
    _mount(env)
    assert env.client.get("/notifications").status_code == 401
    assert env.client.get("/notifications/unread_count").status_code == 401
    assert env.client.post("/notifications/read_all").status_code == 401


def test_a_join_request_tells_those_who_handle_members(env):  # noqa: F811
    _mount(env)
    _members(env)
    s = env.Session()
    s.get(Faction, 1).requires_approval = True
    s.commit()
    s.close()
    r = env.client.post(
        "/join_requests", json={"faction_id": 1}, headers=env.h("newbie")
    )
    assert r.status_code == 201

    for who in ("alice", "adele"):  # the leader and the officer
        notes = _mine(env, who)
        assert [n["kind"] for n in notes] == ["join_request"]
        assert "newbie" in notes[0]["message"]
        assert notes[0]["link"] == "/faction/1"
    assert _kinds(env, "rory") == []  # no handle_members
    assert _kinds(env, "newbie") == []

    # The answer reaches the applicant
    request_id = r.json()["request_id"]
    r = env.client.post(f"/join_requests/{request_id}/accept", headers=env.h("alice"))
    assert r.status_code == 200
    assert _kinds(env, "newbie") == ["join_accepted"]


def test_a_refused_request_is_told(env):  # noqa: F811
    _mount(env)
    s = env.Session()
    s.get(Faction, 1).requires_approval = True
    s.commit()
    s.close()
    rid = env.client.post(
        "/join_requests", json={"faction_id": 1}, headers=env.h("newbie")
    ).json()["request_id"]
    env.client.post(f"/join_requests/{rid}/refuse", headers=env.h("alice"))
    assert _kinds(env, "newbie") == ["join_refused"]


def test_being_removed_or_made_leader_is_told(env):  # noqa: F811
    _mount(env)
    _members(env)
    env.client.post("/users/11/kick", headers=env.h("alice"))
    assert _kinds(env, "rory") == ["kicked"]

    env.client.post(
        "/factions/transfer/1", json={"user_id": 10}, headers=env.h("alice")
    )
    assert _kinds(env, "adele") == ["leadership"]


def test_deleting_a_faction_tells_its_members_but_not_the_leader(env):  # noqa: F811
    _mount(env)
    _members(env)
    assert (
        env.client.delete("/factions/delete/1", headers=env.h("alice")).status_code
        == 204
    )
    assert _kinds(env, "rory") == ["faction_deleted"]
    assert _kinds(env, "adele") == ["faction_deleted"]
    assert _kinds(env, "alice") == []


def test_an_accepted_offer_tells_its_owner(env):  # noqa: F811
    _mount(env)
    r = env.client.post(
        "/offers/create",
        json={
            "offer_type": "SELL",
            "item_description": "épée",
            "currency_name": "Diamant",
            "price_per_unit": 2,
            "quantity": 5,
            "user_id": 1,
        },
        headers=env.h("alice"),
    )
    assert r.status_code == 201
    oid = r.json()["offer_id"]
    r = env.client.post(
        f"/offers/accept/{oid}",
        json={"buyer_user_id": 2, "quantity": 1},
        headers=env.h("newbie"),
    )
    assert r.status_code in (200, 202), r.text
    notes = _mine(env, "alice")
    assert [n["kind"] for n in notes] == ["offer_accepted"]
    assert "newbie" in notes[0]["message"] and "épée" in notes[0]["message"]
    assert _kinds(env, "newbie") == []


def test_reading_marks_and_counts(env):  # noqa: F811
    _mount(env)
    _members(env)
    env.client.post("/users/11/kick", headers=env.h("alice"))
    s = env.Session()
    s.add(Notification(user_id=11, kind="x", message="second"))
    s.commit()
    s.close()

    count = lambda: env.client.get(  # noqa: E731
        "/notifications/unread_count", headers=env.h("rory")
    ).json()["count"]
    assert count() == 2
    assert [n["message"] for n in _mine(env, "rory")][0] == "second"  # newest first
    assert len(_mine(env, "rory", unread_only=True)) == 2

    first = _mine(env, "rory")[0]["notification_id"]
    r = env.client.post(f"/notifications/{first}/read", headers=env.h("rory"))
    assert r.status_code == 200 and r.json()["is_read"] is True
    assert count() == 1
    assert len(_mine(env, "rory", unread_only=True)) == 1

    r = env.client.post("/notifications/read_all", headers=env.h("rory"))
    assert r.json() == {"count": 0}
    assert count() == 0
    assert len(_mine(env, "rory")) == 2  # still there, read


def test_nobody_reads_somebody_elses(env):  # noqa: F811
    _mount(env)
    _members(env)
    env.client.post("/users/11/kick", headers=env.h("alice"))
    nid = _mine(env, "rory")[0]["notification_id"]
    assert (
        env.client.post(
            f"/notifications/{nid}/read", headers=env.h("alice")
        ).status_code
        == 404
    )
    assert (
        env.client.post(
            f"/notifications/{nid}/read", headers=env.h("newbie")
        ).status_code
        == 404
    )
    assert _mine(env, "alice") == []
    # Marking all as read only touches the caller's
    env.client.post("/notifications/read_all", headers=env.h("alice"))
    count = env.client.get("/notifications/unread_count", headers=env.h("rory")).json()[
        "count"
    ]
    assert count == 1


def test_only_the_newest_hundred_are_kept(env):  # noqa: F811
    _mount(env)
    s = env.Session()
    s.add_all(Notification(user_id=1, kind="x", message=f"n{i}") for i in range(105))
    s.commit()
    s.close()
    notes = _mine(env, "alice", limit=100)
    assert len(notes) == 100
    assert notes[0]["message"] == "n104"
    s = env.Session()
    assert s.query(Notification).filter_by(user_id=1).count() == 100
    s.close()


def test_paging_and_bad_limits(env):  # noqa: F811
    _mount(env)
    s = env.Session()
    s.add_all(Notification(user_id=1, kind="x", message=f"n{i}") for i in range(5))
    s.commit()
    s.close()
    assert [n["message"] for n in _mine(env, "alice", limit=2, skip=1)] == ["n3", "n2"]
    for params in ({"limit": 0}, {"limit": 101}, {"skip": -1}):
        r = env.client.get("/notifications", params=params, headers=env.h("alice"))
        assert r.status_code == 422


def test_a_new_role_is_told(env):  # noqa: F811
    _mount(env)
    _members(env)
    r = env.client.patch(
        "/users/update/11", json={"role_id": 30}, headers=env.h("alice")
    )
    assert r.status_code == 200, r.text
    notes = _mine(env, "rory")
    assert [n["kind"] for n in notes] == ["role_changed"]
    assert "Chef Adjoint" in notes[0]["message"]
