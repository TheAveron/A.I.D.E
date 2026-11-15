"""Offers can be addressed to listed users and to the members of listed factions."""

from test_hardening import PW_HASH, env  # noqa: F401  (pytest fixture)

from app.database import Faction, Role, User

OFFER = {
    "offer_type": "SELL",
    "item_description": "épée",
    "currency_name": "Diamant",
    "price_per_unit": 1,
    "quantity": 10,
    "user_id": 1,
}


def _world(env):  # noqa: F811
    """alice (Alpha), newbie (Sans Faction) and Beta's carl and dora."""
    s = env.Session()
    s.add(Faction(faction_id=2, name="Beta", is_approved=True))
    s.commit()
    s.add_all(
        [
            Role(role_id=40, name="Membre", faction_id=2, accept_offers=True),
            User(
                user_id=5,
                username="carl",
                hashed_password=PW_HASH,
                faction_id=2,
                role_id=40,
            ),
            User(user_id=6, username="eve", hashed_password=PW_HASH),
        ]
    )
    s.commit()
    s.close()


def _sell(env, **over):  # noqa: F811
    return env.client.post(
        "/offers/create", json={**OFFER, **over}, headers=env.h("alice")
    )


def _listed(env, who=None):  # noqa: F811
    headers = env.h(who) if who else {}
    r = env.client.get("/offers/list", headers=headers)
    assert r.status_code == 200
    return {o["offer_id"] for o in r.json()}


def _status(env, offer_id, who=None):  # noqa: F811
    headers = env.h(who) if who else {}
    return env.client.get(f"/offers/detail/{offer_id}", headers=headers).status_code


def test_an_offer_without_lists_stays_public(env):  # noqa: F811
    offer = _sell(env).json()
    assert offer["is_private"] is False
    assert offer["offer_id"] in _listed(env)
    assert _status(env, offer["offer_id"]) == 200


def test_empty_lists_mean_public(env):  # noqa: F811
    offer = _sell(env, allowed_user_ids=[], allowed_faction_ids=[]).json()
    assert offer["is_private"] is False
    assert offer["allowed_user_ids"] is None


def test_a_private_offer_is_seen_by_its_audience_only(env):  # noqa: F811
    _world(env)
    offer = _sell(env, allowed_user_ids=[2, 2], allowed_faction_ids=[2]).json()
    oid = offer["offer_id"]
    assert offer["is_private"] is True
    assert offer["allowed_user_ids"] == [2]  # duplicates dropped

    for who in ("alice", "newbie", "carl"):  # owner, listed user, listed faction
        assert oid in _listed(env, who), who
        assert _status(env, oid, who) == 200, who
    for who in (None, "eve"):  # anonymous, outsider
        assert oid not in _listed(env, who), who
        assert _status(env, oid, who) == 404, who


def test_listing_filters_keep_working_with_private_offers(env):  # noqa: F811
    _world(env)
    private = _sell(env, allowed_user_ids=[2]).json()["offer_id"]
    public = _sell(env).json()["offer_id"]
    r = env.client.get("/offers/list?limit=1", headers=env.h("eve"))
    assert [o["offer_id"] for o in r.json()] == [public]
    r = env.client.get("/offers/list?limit=5", headers=env.h("newbie"))
    assert {o["offer_id"] for o in r.json()} == {public, private}


def test_only_the_audience_can_accept(env):  # noqa: F811
    _world(env)
    oid = _sell(env, allowed_faction_ids=[2]).json()["offer_id"]

    def accept(who, **body):
        return env.client.post(
            f"/offers/accept/{oid}", json=body, headers=env.h(who)
        ).status_code

    assert accept("eve", buyer_user_id=6, quantity=1) == 404
    assert accept("newbie", buyer_user_id=2, quantity=1) == 404
    assert accept("carl", buyer_user_id=5, quantity=1) == 202
    # The offer is still there for the audience afterwards
    assert oid in _listed(env, "carl")


def test_unknown_ids_are_refused(env):  # noqa: F811
    assert _sell(env, allowed_user_ids=[999]).status_code == 400
    assert _sell(env, allowed_faction_ids=[999]).status_code == 400
    assert _sell(env, allowed_user_ids=[0]).status_code == 422


def test_the_owner_can_open_or_close_the_audience(env):  # noqa: F811
    _world(env)
    oid = _sell(env, allowed_user_ids=[2]).json()["offer_id"]
    assert _status(env, oid, "eve") == 404

    r = env.client.put(
        f"/offers/update/{oid}",
        json={"allowed_user_ids": [6]},
        headers=env.h("alice"),
    )
    assert r.status_code == 202
    assert _status(env, oid, "eve") == 200
    assert _status(env, oid, "newbie") == 404

    r = env.client.put(
        f"/offers/update/{oid}",
        json={"allowed_user_ids": None},
        headers=env.h("alice"),
    )
    assert r.status_code == 202
    assert r.json()["is_private"] is False
    assert _status(env, oid, "newbie") == 200


def test_a_bad_token_is_still_a_401(env):  # noqa: F811
    r = env.client.get("/offers/list", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def _search(env, query, who="alice"):  # noqa: F811
    r = env.client.get(f"/offers/list?{query}", headers=env.h(who))
    assert r.status_code == 200, r.text
    return [o["item_description"] for o in r.json()]


def test_offers_can_be_filtered_by_type_text_and_price(env):  # noqa: F811
    _sell(env, item_description="Épée en fer", price_per_unit=5)
    _sell(env, item_description="Pioche 100%", price_per_unit=2)
    _sell(env, item_description="Arc_long", price_per_unit=9, offer_type="BUY")

    assert sorted(_search(env, "offer_type=BUY")) == ["Arc_long"]
    assert sorted(_search(env, "offer_type=SELL")) == ["Pioche 100%", "Épée en fer"]
    assert _search(env, "q=PIOCHE") == ["Pioche 100%"]
    assert sorted(_search(env, "min_price=5")) == ["Arc_long", "Épée en fer"]
    assert _search(env, "max_price=2") == ["Pioche 100%"]
    assert _search(env, "min_price=3&max_price=6") == ["Épée en fer"]
    assert _search(env, "q=er&offer_type=SELL") == ["Épée en fer"]


def test_wildcards_in_the_search_are_plain_characters(env):  # noqa: F811
    _sell(env, item_description="Pioche 100%")
    _sell(env, item_description="Arc_long")
    _sell(env, item_description="Arcxlong")
    assert _search(env, "q=%25") == ["Pioche 100%"]
    assert _search(env, "q=c_l") == ["Arc_long"]


def test_bad_filters_are_422(env):  # noqa: F811
    for query in ("offer_type=XX", "min_price=-1", "q=" + "x" * 101):
        r = env.client.get(f"/offers/list?{query}", headers=env.h("alice"))
        assert r.status_code == 422, query


def test_filters_do_not_reveal_private_offers(env):  # noqa: F811
    _world(env)
    _sell(env, item_description="Secret", allowed_user_ids=[2])
    assert _search(env, "q=secret", "eve") == []
    assert _search(env, "q=secret", "newbie") == ["Secret"]
