"""The reason given when a currency's total changes lands in its audit trail."""

from test_hardening import env  # noqa: F401  (pytest fixture)


def update(env, **body):  # noqa: F811
    return env.client.put("/currencies/update/1", json=body, headers=env.h("alice"))


def history(env):  # noqa: F811
    r = env.client.get("/currencies/history/1", headers=env.h("alice"))
    assert r.status_code == 200, r.text
    return r.json()


def test_the_note_is_kept_with_the_change(env):  # noqa: F811
    assert (
        update(env, total_in_circulation=50, notes="  Frappe du mois  ").status_code
        == 202
    )
    entry = history(env)[0]
    assert entry["notes"] == "Frappe du mois"
    assert (entry["old_total_in_circulation"], entry["new_total_in_circulation"]) == (
        0,
        50,
    )


def test_a_blank_note_is_stored_as_nothing(env):  # noqa: F811
    update(env, total_in_circulation=5, notes="   ")
    assert history(env)[0]["notes"] is None


def test_a_note_alone_creates_no_entry(env):  # noqa: F811
    assert update(env, notes="rien n'a changé").status_code == 202
    assert history(env) == []


def test_an_overlong_note_is_a_422(env):  # noqa: F811
    assert update(env, total_in_circulation=5, notes="x" * 501).status_code == 422


def test_a_currency_with_history_can_be_deleted(env):  # noqa: F811
    h = env.h("alice")
    r = env.client.put(
        "/currencies/update/1",
        json={"total_in_circulation": 5, "notes": "first"},
        headers=h,
    )
    assert r.status_code == 202
    assert env.client.delete("/currencies/delete/1", headers=h).status_code == 204
    assert env.client.get("/currencies/faction/1", headers=h).json() is None
