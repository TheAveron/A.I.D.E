"""The "Membre" role: where new members land, so it can't go away."""

from test_hardening import env  # noqa: F401  (pytest fixture)

from app.database import Role


def _add_member_role(env):  # noqa: F811
    s = env.Session()
    s.add(Role(role_id=50, name="Membre", faction_id=1, view_transactions=True))
    s.commit()
    s.close()


def test_the_member_role_cant_be_renamed_or_deleted(env):  # noqa: F811
    _add_member_role(env)
    h = env.h("alice")  # Chef of Alpha, with manage_roles
    r = env.client.put("/roles/update/50", json={"name": "Recrue"}, headers=h)
    assert r.status_code == 403
    r = env.client.delete("/roles/delete/50", headers=h)
    assert r.status_code == 403
    # Its permissions may still change
    r = env.client.put("/roles/update/50", json={"view_transactions": False}, headers=h)
    assert r.status_code == 200, r.text


def test_nobody_else_takes_the_name(env):  # noqa: F811
    _add_member_role(env)
    h = env.h("alice")
    r = env.client.post(
        "/roles/faction/1/create", json={"name": "Membre", "faction_id": 1}, headers=h
    )
    assert r.status_code == 403
    s = env.Session()
    s.add(Role(role_id=51, name="Trésorier", faction_id=1))
    s.commit()
    s.close()
    r = env.client.put("/roles/update/51", json={"name": "Membre"}, headers=h)
    assert r.status_code == 403
