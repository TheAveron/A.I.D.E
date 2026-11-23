"""The real application (main.py): its wiring is not covered by the tests that
build their own small FastAPI apps, so a mistake there would go unnoticed.

main.py mounts folders that only exist after a frontend build; the tests make
StaticFiles accept missing ones and run from a temporary directory (main.py
writes logs/ relative to the current directory).
"""

import asyncio
import importlib
import logging
import sys

import pytest
from fastapi.testclient import TestClient
from starlette.staticfiles import StaticFiles

from app.core.logger import log_safe


@pytest.fixture
def main_app(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    original_init = StaticFiles.__init__

    def lenient_init(self, *args, **kwargs):
        kwargs["check_dir"] = False
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(StaticFiles, "__init__", lenient_init)
    sys.modules.pop("main", None)
    module = importlib.import_module("main")
    yield module.app
    sys.modules.pop("main", None)
    for handler in list(logging.getLogger("aide").handlers):
        logging.getLogger("aide").removeHandler(handler)
        handler.close()


def test_validation_errors_do_not_echo_the_input(main_app):
    client = TestClient(main_app, raise_server_exceptions=False)
    secret = "a" * 100
    r = client.post("/auth/register", json={"username": "u", "password": secret})
    assert r.status_code == 422
    assert secret not in r.text
    assert all("input" not in error for error in r.json()["detail"])


def test_non_finite_numbers_are_a_422_not_a_500(main_app):
    client = TestClient(main_app, raise_server_exceptions=False)
    body = (
        '{"offer_type": "SELL", "item_description": "x", "currency_name": "D", '
        '"price_per_unit": Infinity, "quantity": 1, "user_id": 1}'
    )
    r = client.post(
        "/offers/create", content=body, headers={"Content-Type": "application/json"}
    )
    # 401 would also be fine for the app (no token); what matters is no 500.
    assert r.status_code in (401, 422)


def _get_through_asgi(app, path: str) -> None:
    """GET `path` (already percent-decoded, as a server hands it to the app).

    The test client can't be used: it refuses or rewrites control characters in
    URLs, while a raw socket client can send them percent-encoded.
    """

    async def call():
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [(b"host", b"testserver")],
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "root_path": "",
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            pass

        try:
            await app(scope, receive, send)
        except RuntimeError:
            pass  # no frontend build here: the catch-all route has no index.html

    asyncio.run(call())


def test_control_characters_in_a_path_are_not_written_to_the_log(main_app, caplog):
    with caplog.at_level(logging.DEBUG, logger="aide"):
        _get_through_asgi(main_app, "/nothing\x1b[2Jcleared")
    messages = [r.getMessage() for r in caplog.records if "nothing" in r.getMessage()]
    assert messages, "the request was not logged at all"
    assert all("\x1b" not in m for m in messages)
    assert any("\\x1b[2Jcleared" in m for m in messages)


def test_log_safe_makes_control_characters_visible():
    assert log_safe("a\nb\rc\td\x00e") == "a\\x0ab\\x0dc\\x09d\\x00e"
    assert log_safe("/plain/path-é") == "/plain/path-é"


def test_files_of_the_frontend_build_are_served_not_index_html(
    main_app, monkeypatch, tmp_path
):
    import main

    client_dir = tmp_path / "build" / "client"
    (client_dir / "images").mkdir(parents=True)
    (client_dir / "images" / "formula.png").write_bytes(b"PNGDATA")
    (client_dir / "index.html").write_text("<html>spa</html>")
    (tmp_path / "secret.txt").write_text("not in the build")
    monkeypatch.setattr(main, "frontend_dist_path", tmp_path / "build")

    client = TestClient(main_app, raise_server_exceptions=False)
    page = {"Accept": "text/html,application/xhtml+xml"}

    assert client.get("/images/formula.png").content == b"PNGDATA"
    # Client-side routes opened by a browser still get the SPA
    assert client.get("/factions", headers=page).text == "<html>spa</html>"
    # Nothing outside the build is reachable
    assert "not in the build" not in client.get("/%2e%2e/%2e%2e/secret.txt").text
    assert (
        "not in the build"
        not in client.get("/images/%2e%2e/%2e%2e/%2e%2e/secret.txt", headers=page).text
    )


def test_unknown_paths_are_a_404_not_the_spa(main_app, monkeypatch, tmp_path):
    import main

    client_dir = tmp_path / "build" / "client"
    client_dir.mkdir(parents=True)
    (client_dir / "index.html").write_text("<html>spa</html>")
    monkeypatch.setattr(main, "frontend_dist_path", tmp_path / "build")

    client = TestClient(main_app, raise_server_exceptions=False)
    page = {"Accept": "text/html,application/xhtml+xml"}

    # A missing file and a scanner's probe: never the SPA, even when the
    # request pretends to be a browser
    for path in (
        "/images/missing.png",
        "/officescan/console/html/cgi/cgiShowClientAdm.exe",
        "/.env",
        "/login.aspx",
    ):
        r = client.get(path, headers=page)
        assert r.status_code == 404, path
        assert "<html>" not in r.text, path

    # A request that doesn't ask for HTML (API client, scanner) gets a 404 too
    assert client.get("/owa/").status_code == 404
    assert (
        client.get(
            "/no-such-route", headers={"Accept": "application/json, text/plain, */*"}
        ).status_code
        == 404
    )

    # ... while a browser opening a client-side route gets the SPA
    assert client.get("/owa/", headers=page).text == "<html>spa</html>"
    assert client.get("/faction/3", headers=page).text == "<html>spa</html>"


def test_pages_sharing_a_path_with_the_api_get_the_spa(main_app, monkeypatch, tmp_path):
    """/trains is both a page and GET /trains: a browser reloading the page
    must get the React app, an API client the JSON."""
    import main

    client_dir = tmp_path / "build" / "client"
    client_dir.mkdir(parents=True)
    (client_dir / "index.html").write_text("<html>spa</html>")
    monkeypatch.setattr(main, "frontend_dist_path", tmp_path / "build")

    client = TestClient(main_app, raise_server_exceptions=False)
    page = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
    axios = {"Accept": "application/json, text/plain, */*"}

    for path in ("/trains", "/trains/new", "/lines", "/stations", "/notifications"):
        r = client.get(path, headers=page)
        assert r.status_code == 200, path
        assert r.text == "<html>spa</html>", path

    # API clients still reach the routes. No auth here: /notifications is a
    # 401, and /trains/new (GET /trains/{id}) a 422, but JSON either way.
    for path in ("/trains/new", "/notifications"):
        r = client.get(path, headers=axios)
        assert r.status_code in (401, 422), path
        assert r.headers["content-type"].startswith("application/json"), path
    # A non-GET with a browser's Accept is never the SPA
    assert "<html>" not in client.post("/trains/", headers=page).text


def test_docs_and_static_folders_are_not_replaced_by_the_spa(
    main_app, monkeypatch, tmp_path
):
    import main

    client_dir = tmp_path / "build" / "client"
    client_dir.mkdir(parents=True)
    (client_dir / "index.html").write_text("<html>spa</html>")
    monkeypatch.setattr(main, "frontend_dist_path", tmp_path / "build")

    client = TestClient(main_app, raise_server_exceptions=False)
    page = {"Accept": "text/html,application/xhtml+xml"}

    docs = client.get("/docs", headers=page)
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower()
    assert "spa" not in client.get("/redoc", headers=page).text
    assert client.get("/openapi.json", headers=page).json()["openapi"]
    # The mounted folders answer themselves (here: missing directories)
    for path in ("/maps/nothing", "/assets/nothing"):
        assert "<html>spa</html>" not in client.get(path, headers=page).text, path


def test_without_a_frontend_build_html_requests_reach_the_api(
    main_app, monkeypatch, tmp_path
):
    import main

    monkeypatch.setattr(main, "frontend_dist_path", tmp_path / "no-build")
    client = TestClient(main_app, raise_server_exceptions=False)
    r = client.get("/notifications", headers={"Accept": "text/html"})
    assert r.status_code == 401
