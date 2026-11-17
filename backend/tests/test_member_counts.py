"""GET /factions/member_counts: one query instead of one request per faction."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.database import Faction, User


def test_counts_every_faction_including_empty_ones(env):  # noqa: F811
    s = env.Session()
    s.add(Faction(faction_id=7, name="Vide", is_approved=True))
    s.add(User(user_id=3, username="bob", hashed_password=PW_HASH, faction_id=1))
    s.commit()
    s.close()

    res = env.client.get("/factions/member_counts")

    assert res.status_code == 200
    assert res.json() == {"1": 2, "3": 1, "7": 0}


def test_counts_match_the_per_faction_member_lists(env):  # noqa: F811
    counts = env.client.get("/factions/member_counts").json()
    for faction_id, count in counts.items():
        members = env.client.get(f"/users/faction/{faction_id}").json()
        assert len(members) == count


def test_the_route_is_not_shadowed_by_the_detail_route(env):  # noqa: F811
    assert env.client.get("/factions/detail/1").json()["name"] == "Alpha"
    assert env.client.get("/factions/member_counts").status_code == 200
