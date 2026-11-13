"""Third backend pass: bounded inputs, error messages that don't leak server
paths, and the limit on failed logins.

Uses the `env` fixture of test_hardening.py (SQLite in memory, a few routers).
"""

import json

import pytest
from fastapi import HTTPException
from test_hardening import env  # noqa: F401  (pytest fixture)

from app.api import documentation
from app.api.auth import login_limiter
from app.core.ratelimit import LoginLimiter
from app.schemas.base import INT32_MAX, MAX_DESCRIPTION_LENGTH, MAX_PRICE

OFFER = {
    "offer_type": "SELL",
    "item_description": "Laser Gun",
    "currency_name": "Diamant",
    "price_per_unit": 5,
    "quantity": 3,
    "faction_id": 1,
}


def post_offer(env, **over):  # noqa: F811
    return env.client.post(
        "/offers/create", json={**OFFER, **over}, headers=env.h("alice")
    )


def post_raw_offer(env, raw_fragment):  # noqa: F811
    """Send a body Python's own JSON encoder would refuse to produce."""
    body = json.dumps({**OFFER, "price_per_unit": 0}).replace(
        '"price_per_unit": 0', raw_fragment
    )
    return env.client.post(
        "/offers/create",
        content=body,
        headers={**env.h("alice"), "Content-Type": "application/json"},
    )


# ------------------------------------------------------------------- offers
class TestOfferBounds:
    @pytest.mark.parametrize(
        "fragment",
        [
            '"price_per_unit": Infinity',
            '"price_per_unit": -Infinity',
            '"price_per_unit": NaN',
        ],
    )
    def test_non_finite_prices_are_a_422(self, env, fragment):  # noqa: F811
        assert post_raw_offer(env, fragment).status_code == 422

    def test_a_rejected_infinite_price_does_not_poison_the_listing(
        self, env
    ):  # noqa: F811
        post_raw_offer(env, '"price_per_unit": Infinity')
        assert post_offer(env).status_code == 201
        r = env.client.get("/offers/list")
        assert r.status_code == 200 and len(r.json()) == 1

    def test_price_has_an_upper_bound(self, env):  # noqa: F811
        assert post_offer(env, price_per_unit=MAX_PRICE).status_code == 201
        assert post_offer(env, price_per_unit=MAX_PRICE * 10).status_code == 422
        assert post_offer(env, price_per_unit=1e300).status_code == 422

    def test_quantity_must_fit_the_integer_column(self, env):  # noqa: F811
        assert post_offer(env, quantity=INT32_MAX).status_code == 201
        assert post_offer(env, quantity=INT32_MAX + 1).status_code == 422
        assert post_offer(env, quantity=10**30).status_code == 422

    def test_updates_have_the_same_bounds(self, env):  # noqa: F811
        offer_id = post_offer(env).json()["offer_id"]
        h = env.h("alice")
        url = f"/offers/update/{offer_id}"
        assert (
            env.client.put(url, json={"quantity": INT32_MAX + 1}, headers=h).status_code
            == 422
        )
        assert (
            env.client.put(
                url, json={"price_per_unit": MAX_PRICE * 10}, headers=h
            ).status_code
            == 422
        )
        r = env.client.put(url, json={"quantity": INT32_MAX}, headers=h)
        assert r.status_code == 202

    def test_allowed_parties_is_capped(self, env):  # noqa: F811
        assert post_offer(env, allowed_parties=list(range(1000))).status_code == 201
        assert post_offer(env, allowed_parties=list(range(1001))).status_code == 422


# ---------------------------------------------------------------- other input
class TestOtherBounds:
    def test_total_in_circulation_must_fit_the_integer_column(self, env):  # noqa: F811
        h = env.h("alice")
        r = env.client.put(
            "/currencies/update/Diamant",
            json={"total_in_circulation": INT32_MAX + 1},
            headers=h,
        )
        assert r.status_code == 422
        r = env.client.put(
            "/currencies/update/Diamant",
            json={"total_in_circulation": INT32_MAX},
            headers=h,
        )
        assert r.status_code == 202

    def test_faction_description_is_capped(self, env):  # noqa: F811
        h = env.h("newbie")
        too_long = "x" * (MAX_DESCRIPTION_LENGTH + 1)
        r = env.client.post(
            "/factions/create",
            json={"name": "Gamma", "description": too_long},
            headers=h,
        )
        assert r.status_code == 422
        r = env.client.post(
            "/factions/create",
            json={"name": "Gamma", "description": "x" * MAX_DESCRIPTION_LENGTH},
            headers=h,
        )
        assert r.status_code == 201

    def test_role_description_is_capped(self, env):  # noqa: F811
        body = {
            "name": "Scribe",
            "faction_id": 1,
            "description": "x" * (MAX_DESCRIPTION_LENGTH + 1),
        }
        r = env.client.post(
            "/roles/faction/1/create", json=body, headers=env.h("alice")
        )
        assert r.status_code == 422
        body["description"] = "x" * MAX_DESCRIPTION_LENGTH
        r = env.client.post(
            "/roles/faction/1/create", json=body, headers=env.h("alice")
        )
        assert r.status_code == 201

    def test_currency_history_pagination_is_validated(self, env):
        h = env.h("alice")
        for query in ("?limit=0", "?limit=501", "?skip=-1"):
            r = env.client.get("/currencies/history/Diamant" + query, headers=h)
            assert r.status_code == 422, query
        r = env.client.get("/currencies/history/Diamant?limit=500", headers=h)
        assert r.status_code == 200

    def test_faction_list_pagination_is_validated(self, env):
        for query in ("?limit=0", "?limit=501", "?skip=-1"):
            assert env.client.get("/factions/list" + query).status_code == 422, query
        assert env.client.get("/factions/list?limit=500").status_code == 200

    def test_history_pagination_is_validated(self, env):  # noqa: F811
        h = env.h("alice")
        for query in ("?limit=0", "?limit=501", "?skip=-1"):
            assert (
                env.client.get("/history" + query, headers=h).status_code == 422
            ), query
        assert env.client.get("/history?limit=500&skip=0", headers=h).status_code == 200


# ---------------------------------------------------------------- documents
class TestDocumentLimits:
    @pytest.fixture(autouse=True)
    def docs_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
        self.root = tmp_path / "documents"

    def create(self, env, title="Reglement", content="x"):  # noqa: F811
        return env.client.post(
            "/documents/create",
            json={"title": title, "content": content},
            headers=env.h("alice"),
        )

    def test_title_and_content_sizes_are_bounded(self, env):  # noqa: F811
        assert (
            self.create(
                env, title="a" * (documentation.MAX_TITLE_LENGTH + 1)
            ).status_code
            == 422
        )
        r = self.create(env, content="x" * (documentation.MAX_CONTENT_LENGTH + 1))
        assert r.status_code == 422
        assert (
            self.create(env, content="x" * documentation.MAX_CONTENT_LENGTH).status_code
            == 201
        )

    def test_a_title_whose_file_name_is_too_long_is_a_400(self, env):  # noqa: F811
        # 100 characters, 3 bytes each: short as a title, too long as a file name
        r = self.create(env, title="日" * 100)
        assert r.status_code == 400 and "too long" in r.json()["detail"]

    def test_write_errors_do_not_reveal_server_paths(self, env, tmp_path):  # noqa: F811
        # DOCS_DIR is a regular file, so creating folders under it fails.
        blocker = tmp_path / "blocker"
        blocker.write_text("not a folder")
        documentation.DOCS_DIR = blocker
        r = self.create(env)
        assert r.status_code == 500
        assert r.json()["detail"] == "Could not save the document"
        assert str(tmp_path) not in r.text

    def test_read_errors_do_not_reveal_server_paths(
        self, env, monkeypatch
    ):  # noqa: F811
        folder = self.root / "AOS"
        folder.mkdir(parents=True)
        (folder / "doc.md").write_text("hello")

        def broken(self, *a, **k):
            raise PermissionError(f"[Errno 13] Permission denied: '{self}'")

        monkeypatch.setattr(type(folder), "read_text", broken)
        r = env.client.get("/documents/AOS/doc/doc")
        assert r.status_code == 500
        assert str(self.root) not in r.text

    def test_a_folder_name_with_a_trailing_newline_is_refused(self):
        # "$" matches before a final newline, so such a name used to pass.
        with pytest.raises(HTTPException) as exc:
            documentation._document_path("AOS\n", doc_name="x")
        assert exc.value.status_code == 404

    @pytest.mark.parametrize("folder", ["..", "a/b", "a\\b", "", ".", "a\x00b"])
    def test_other_odd_folder_names_are_refused(self, folder):
        with pytest.raises(HTTPException):
            documentation._document_path(folder, doc_name="x")


# ------------------------------------------------------------ failed logins
class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class TestLoginLimiter:
    def make(self, **kw):
        clock = FakeClock()
        return (
            LoginLimiter(clock=clock, **{"max_failures": 3, "window": 60, **kw}),
            clock,
        )

    def test_locks_after_max_failures_then_expires(self):
        limiter, clock = self.make()
        for _ in range(2):
            limiter.record_failure("k")
        assert limiter.retry_after("k") == 0
        limiter.record_failure("k")
        assert limiter.retry_after("k") > 0
        clock.now += 59
        assert limiter.retry_after("k") > 0
        clock.now += 2
        assert limiter.retry_after("k") == 0

    def test_retry_after_counts_down_to_the_oldest_failure_leaving(self):
        limiter, clock = self.make()
        for _ in range(3):
            limiter.record_failure("k")
        assert 59 <= limiter.retry_after("k") <= 61
        clock.now += 30
        assert 29 <= limiter.retry_after("k") <= 31

    def test_keys_are_independent_and_reset_clears_one(self):
        limiter, _ = self.make()
        for _ in range(3):
            limiter.record_failure("a")
        assert limiter.retry_after("a") > 0 and limiter.retry_after("b") == 0
        limiter.reset("a")
        assert limiter.retry_after("a") == 0

    def test_old_failures_stop_counting(self):
        limiter, clock = self.make()
        limiter.record_failure("k")
        limiter.record_failure("k")
        clock.now += 61
        limiter.record_failure("k")
        assert limiter.retry_after("k") == 0

    def test_memory_stays_bounded(self):
        limiter, _ = self.make(max_keys=50)
        for i in range(500):
            limiter.record_failure(f"user{i}")
        assert len(limiter._failures) <= 50


class TestLoginEndpointIsRateLimited:
    def login(self, env, username="alice", password="pw"):  # noqa: F811
        return env.client.post(
            "/auth/login", json={"username": username, "password": password}
        )

    def test_eleventh_wrong_password_is_a_429_with_retry_after(self, env):  # noqa: F811
        for _ in range(10):
            assert self.login(env, password="wrong").status_code == 401
        r = self.login(env, password="wrong")
        assert r.status_code == 429
        assert int(r.headers["Retry-After"]) > 0

    def test_the_right_password_is_refused_while_locked(self, env):  # noqa: F811
        for _ in range(10):
            self.login(env, password="wrong")
        assert self.login(env).status_code == 429

    def test_other_accounts_are_not_affected(self, env):  # noqa: F811
        for _ in range(10):
            self.login(env, password="wrong")
        assert self.login(env, username="newbie").status_code == 202

    def test_a_success_clears_the_count(self, env):  # noqa: F811
        for _ in range(9):
            self.login(env, password="wrong")
        assert self.login(env).status_code == 202
        for _ in range(9):
            assert self.login(env, password="wrong").status_code == 401
        assert self.login(env).status_code == 202

    def test_unknown_usernames_are_counted_too(self, env):  # noqa: F811
        for _ in range(10):
            assert self.login(env, username="ghost", password="x").status_code == 401
        assert self.login(env, username="ghost", password="x").status_code == 429

    def test_the_lock_ends_with_the_window(self, env, monkeypatch):  # noqa: F811
        clock = FakeClock()
        monkeypatch.setattr(login_limiter, "_clock", clock)
        for _ in range(10):
            self.login(env, password="wrong")
        assert self.login(env).status_code == 429
        clock.now += login_limiter.window + 1
        assert self.login(env).status_code == 202
