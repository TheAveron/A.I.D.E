"""The reason given when a currency's total changes lands in its audit trail."""

from test_hardening import env  # noqa: F401  (pytest fixture)


def update(env, **body):  # noqa: F811
    return env.client.put(
        "/currencies/update/Diamant", json=body, headers=env.h("alice")
    )


def history(env):  # noqa: F811
    r = env.client.get("/currencies/history/Diamant", headers=env.h("alice"))
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
