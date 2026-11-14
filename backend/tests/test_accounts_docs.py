"""Usernames can't differ only by case; a faction's documents are capped."""

from test_hardening import documentation, env  # noqa: F401  (pytest fixture)


def _register(env, name):  # noqa: F811
    return env.client.post("/auth/register", json={"username": name, "password": "pw"})


def test_a_name_differing_only_by_case_is_taken(env):  # noqa: F811
    assert _register(env, "Mallory").status_code == 201
    assert _register(env, "mallory").status_code == 409
    assert _register(env, "MALLORY").status_code == 409


def test_the_exact_old_names_still_log_in(env):  # noqa: F811
    _register(env, "Carol")
    r = env.client.post("/auth/login", json={"username": "Carol", "password": "pw"})
    assert r.status_code == 202


def test_a_faction_can_only_hold_so_many_documents(
    env, monkeypatch, tmp_path  # noqa: F811
):
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    monkeypatch.setattr(documentation, "MAX_DOCUMENTS_PER_FACTION", 2)
    h = env.h("alice")

    def create(title):
        return env.client.post(
            "/documents/create", json={"title": title, "content": "x"}, headers=h
        )

    assert create("alpha").status_code == 201
    assert create("beta").status_code == 201
    r = create("gamma")
    assert r.status_code == 400
    assert "at most 2" in r.json()["detail"]
    # Existing documents stay readable and nothing was written for the refused one
    assert not (tmp_path / "documents" / "AOS" / "alpha" / "gamma.md").exists()


def test_a_faction_lists_its_documents(env, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    h = env.h("alice")
    faction_id = env.client.get("/users/me", headers=h).json()["faction_id"]

    assert env.client.get(f"/documents/faction/{faction_id}").json() == []

    for title in ("Règles du jeu", "alpha"):
        r = env.client.post(
            "/documents/create", json={"title": title, "content": "x"}, headers=h
        )
        assert r.status_code == 201

    docs = env.client.get(f"/documents/faction/{faction_id}").json()
    assert [d["title"] for d in docs] == ["alpha", "Règles du jeu"]
    first = docs[0]
    # The listing gives what the document routes need
    r = env.client.get(
        f"/documents/{first['server']}/faction_doc/{first['folder']}/{first['doc_name']}"
    )
    assert r.status_code == 200
    assert r.json()["content"].startswith("# alpha")


def test_listing_the_documents_of_an_unknown_faction_is_a_404(env):  # noqa: F811
    assert env.client.get("/documents/faction/99999").status_code == 404


def test_renaming_a_faction_moves_its_documents(
    env, monkeypatch, tmp_path
):  # noqa: F811
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    h = env.h("alice")
    r = env.client.post(
        "/documents/create", json={"title": "Règles", "content": "x"}, headers=h
    )
    assert r.status_code == 201
    old = tmp_path / "documents" / "AOS" / "alpha"
    assert (old / "regles.md").is_file()

    r = env.client.put("/factions/update/1", json={"name": "Omega"}, headers=h)
    assert r.status_code == 202
    assert not old.exists()
    assert (tmp_path / "documents" / "AOS" / "omega" / "regles.md").is_file()
    docs = env.client.get("/documents/faction/1").json()
    assert [d["doc_name"] for d in docs] == ["regles"]


def test_a_rename_that_keeps_the_folder_name_moves_nothing(
    env, monkeypatch, tmp_path  # noqa: F811
):
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    h = env.h("alice")
    env.client.post(
        "/documents/create", json={"title": "Règles", "content": "x"}, headers=h
    )
    r = env.client.put("/factions/update/1", json={"name": "ALPHA!"}, headers=h)
    assert r.status_code == 202
    assert (tmp_path / "documents" / "AOS" / "alpha" / "regles.md").is_file()


def test_a_rename_onto_an_existing_folder_is_refused(
    env, monkeypatch, tmp_path  # noqa: F811
):
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    h = env.h("alice")
    env.client.post(
        "/documents/create", json={"title": "Règles", "content": "x"}, headers=h
    )
    leftover = tmp_path / "documents" / "AOS" / "omega"
    leftover.mkdir(parents=True)
    r = env.client.put("/factions/update/1", json={"name": "Omega"}, headers=h)
    assert r.status_code == 409
    # Nothing moved, and the name did not change
    assert (tmp_path / "documents" / "AOS" / "alpha" / "regles.md").is_file()
    assert env.client.get("/factions/detail/1").json()["name"] == "Alpha"


def test_a_failed_rename_in_the_database_puts_the_folder_back(
    env, monkeypatch, tmp_path  # noqa: F811
):
    from app.api import faction as faction_api

    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    h = env.h("alice")
    env.client.post(
        "/documents/create", json={"title": "Règles", "content": "x"}, headers=h
    )

    def boom(*args, **kwargs):
        raise ValueError("refused")

    monkeypatch.setattr(faction_api.faction_crud, "update_faction_validation", boom)
    r = env.client.put("/factions/update/1", json={"name": "Omega"}, headers=h)
    assert r.status_code == 400
    assert (tmp_path / "documents" / "AOS" / "alpha" / "regles.md").is_file()
    assert not (tmp_path / "documents" / "AOS" / "omega").exists()
