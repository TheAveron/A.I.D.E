"""Joining a faction that takes members on request only."""

import pytest
from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.api import join_requests
from app.database import Faction, Role, User


@pytest.fixture
def world(env):  # noqa: F811
    """Alpha (leader alice) requires approval; Beta is open; bob has no faction."""
    env.client.app.include_router(join_requests.router)
    s = env.Session()
    alpha = s.get(Faction, 1)
    alpha.requires_approval = True
    s.add(Faction(faction_id=2, name="Beta", is_approved=True))
    s.commit()
    s.add_all(
        [
            Role(role_id=30, name="Invité", faction_id=1),
            Role(role_id=31, name="Chef", faction_id=2, handle_members=True),
            Role(role_id=32, name="Invité", faction_id=2),
            User(user_id=3, username="bob", hashed_password=PW_HASH),
            User(
                user_id=4,
                username="betaleader",
                hashed_password=PW_HASH,
                faction_id=2,
                role_id=31,
            ),
        ]
    )
    s.commit()
    s.close()
    return env


def ask(world, who="bob", faction_id=1, **body):
    return world.client.post(
        "/join_requests",
        json={"faction_id": faction_id, **body},
        headers=world.h(who),
    )


def state(world, user_id):
    s = world.Session()
    user = s.get(User, user_id)
    result = (user.faction_id, user.role_id)
    s.close()
    return result


def test_a_faction_that_requires_approval_cannot_be_joined_directly(world):
    r = world.client.patch(
        "/users/update/3", json={"faction_id": 1}, headers=world.h("bob")
    )
    assert r.status_code == 403
    assert state(world, 3) == (None, None)


def test_an_open_faction_is_still_joined_directly(world):
    r = world.client.patch(
        "/users/update/3", json={"faction_id": 2}, headers=world.h("bob")
    )
    assert r.status_code == 200
    assert state(world, 3) == (2, 32)


def test_asking_an_open_faction_is_pointless(world):
    assert ask(world, faction_id=2).status_code == 400


def test_a_request_is_created_with_a_trimmed_message(world):
    r = ask(world, message="  Salut, je suis nouveau  ")
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["username"], body["faction_id"], body["status"]) == (
        "bob",
        1,
        "PENDING",
    )
    assert body["message"] == "Salut, je suis nouveau"
    assert state(world, 3) == (None, None)  # asking changes nothing by itself


def test_only_one_open_request_per_user(world):
    assert ask(world).status_code == 201
    assert ask(world).status_code == 409


def test_my_request_is_visible_to_me(world):
    assert (
        world.client.get("/join_requests/mine", headers=world.h("bob")).json() is None
    )
    ask(world)
    mine = world.client.get("/join_requests/mine", headers=world.h("bob")).json()
    assert mine["faction_id"] == 1


def test_a_member_cannot_ask_for_their_own_faction_and_a_leader_cannot_leave(world):
    assert ask(world, who="alice", faction_id=1).status_code == 400
    s = world.Session()
    s.get(Faction, 2).requires_approval = True
    s.commit()
    s.close()
    assert ask(world, who="alice", faction_id=2).status_code == 403


def test_the_pending_list_is_for_member_managers_of_that_faction(world):
    ask(world)
    assert (
        world.client.get("/join_requests/faction/1", headers=world.h("bob")).status_code
        == 403
    )
    assert (
        world.client.get(
            "/join_requests/faction/1", headers=world.h("newbie")
        ).status_code
        == 403
    )
    # Another faction's manager has no say on Alpha
    assert (
        world.client.get(
            "/join_requests/faction/1", headers=world.h("betaleader")
        ).status_code
        == 403
    )
    r = world.client.get("/join_requests/faction/1", headers=world.h("alice"))
    assert [x["username"] for x in r.json()] == ["bob"]


def test_accepting_moves_the_applicant_in_as_a_guest(world):
    request_id = ask(world).json()["request_id"]
    r = world.client.post(
        f"/join_requests/{request_id}/accept", headers=world.h("alice")
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ACCEPTED"
    assert state(world, 3) == (1, 30)
    # No longer pending, and a decided request can't be decided again
    assert (
        world.client.get("/join_requests/faction/1", headers=world.h("alice")).json()
        == []
    )
    assert (
        world.client.post(
            f"/join_requests/{request_id}/refuse", headers=world.h("alice")
        ).status_code
        == 409
    )


def test_nobody_else_can_accept(world):
    request_id = ask(world).json()["request_id"]
    for who in ("bob", "newbie", "betaleader"):
        r = world.client.post(
            f"/join_requests/{request_id}/accept", headers=world.h(who)
        )
        assert r.status_code == 403, who
    assert state(world, 3) == (None, None)


def test_refusing_leaves_the_applicant_where_they_were_and_free_to_ask_again(world):
    request_id = ask(world).json()["request_id"]
    r = world.client.post(
        f"/join_requests/{request_id}/refuse", headers=world.h("alice")
    )
    assert r.json()["status"] == "REFUSED"
    assert state(world, 3) == (None, None)
    assert ask(world).status_code == 201


def test_the_applicant_can_withdraw_but_nobody_else(world):
    request_id = ask(world).json()["request_id"]
    assert (
        world.client.delete(
            f"/join_requests/{request_id}", headers=world.h("newbie")
        ).status_code
        == 403
    )
    assert (
        world.client.delete(
            f"/join_requests/{request_id}", headers=world.h("bob")
        ).status_code
        == 204
    )
    assert (
        world.client.get("/join_requests/mine", headers=world.h("bob")).json() is None
    )


def test_accepting_fails_cleanly_when_the_faction_has_no_guest_role(world):
    s = world.Session()
    s.delete(s.get(Role, 30))
    s.commit()
    s.close()
    request_id = ask(world).json()["request_id"]
    r = world.client.post(
        f"/join_requests/{request_id}/accept", headers=world.h("alice")
    )
    assert r.status_code == 400
    assert state(world, 3) == (None, None)


def test_an_applicant_who_became_a_leader_meanwhile_is_not_moved(world):
    request_id = ask(world).json()["request_id"]
    s = world.Session()
    bob = s.get(User, 3)
    bob.faction_id, bob.role_id = 2, 31  # now leads Beta
    s.commit()
    s.close()
    r = world.client.post(
        f"/join_requests/{request_id}/accept", headers=world.h("alice")
    )
    assert r.status_code == 409
    assert state(world, 3) == (2, 31)
    mine = world.client.get("/join_requests/mine", headers=world.h("bob")).json()
    assert mine is None  # the request was closed, not left dangling
