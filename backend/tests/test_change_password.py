"""A user changes their own password, after proving they know the current one."""

from app.api import auth
from test_hardening import env  # noqa: F401  (pytest fixture)


def _change(env, current, new, who="alice"):  # noqa: F811
    return env.client.post(
        "/auth/change-password",
        json={"current_password": current, "new_password": new},
        headers=env.h(who),
    )


def _login(env, password, who="alice"):  # noqa: F811
    return env.client.post(
        "/auth/login", json={"username": who, "password": password}
    ).status_code


def test_the_new_password_replaces_the_old_one(env):  # noqa: F811
    auth.login_limiter.reset("password|1")
    r = _change(env, "pw", "a-better-one")
    assert r.status_code == 200
    assert r.json()["username"] == "alice"
    assert r.json()["access_token"]

    assert _login(env, "a-better-one") == 202
    assert _login(env, "pw") == 401


def test_the_answer_token_works(env):  # noqa: F811
    token = _change(env, "pw", "a-better-one").json()["access_token"]
    r = env.client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_a_wrong_current_password_changes_nothing(env):  # noqa: F811
    r = _change(env, "nope", "a-better-one")
    assert r.status_code == 400
    assert "current password" in r.json()["detail"]
    assert _login(env, "pw") == 202


def test_the_same_password_is_refused(env):  # noqa: F811
    r = _change(env, "pw", "pw")
    assert r.status_code == 400


def test_a_new_password_over_the_bcrypt_limit_is_refused(env):  # noqa: F811
    assert _change(env, "pw", "x" * 73).status_code == 422
    assert _change(env, "pw", "").status_code == 422


def test_it_needs_a_login(env):  # noqa: F811
    r = env.client.post(
        "/auth/change-password",
        json={"current_password": "pw", "new_password": "other"},
    )
    assert r.status_code == 401


def test_guessing_the_current_password_is_limited(env):  # noqa: F811
    auth.login_limiter.reset("password|1")
    for _ in range(10):
        assert _change(env, "nope", "other").status_code == 400
    r = _change(env, "pw", "other")
    assert r.status_code == 429
    assert "Retry-After" in r.headers
    auth.login_limiter.reset("password|1")
