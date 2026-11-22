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
    assert not (tmp_path / "documents" / "AgeOfSteam" / "factions" / "alpha" / "gamma.md").exists()


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
    r = env.client.get(f"/documents/faction/{faction_id}/{first['doc_name']}")
    assert r.status_code == 200
    assert r.json()["title"] == "alpha"


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
    old = tmp_path / "documents" / "AgeOfSteam" / "factions" / "alpha"
    assert (old / "regles.md").is_file()

    r = env.client.put("/factions/update/1", json={"name": "Omega"}, headers=h)
    assert r.status_code == 202
    assert not old.exists()
    assert (tmp_path / "documents" / "AgeOfSteam" / "factions" / "omega" / "regles.md").is_file()
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
    assert (tmp_path / "documents" / "AgeOfSteam" / "factions" / "alpha" / "regles.md").is_file()


def test_a_rename_onto_an_existing_folder_is_refused(
    env, monkeypatch, tmp_path  # noqa: F811
):
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    h = env.h("alice")
    env.client.post(
        "/documents/create", json={"title": "Règles", "content": "x"}, headers=h
    )
    leftover = tmp_path / "documents" / "AgeOfSteam" / "factions" / "omega"
    leftover.mkdir(parents=True)
    r = env.client.put("/factions/update/1", json={"name": "Omega"}, headers=h)
    assert r.status_code == 409
    # Nothing moved, and the name did not change
    assert (tmp_path / "documents" / "AgeOfSteam" / "factions" / "alpha" / "regles.md").is_file()
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
    assert (tmp_path / "documents" / "AgeOfSteam" / "factions" / "alpha" / "regles.md").is_file()
    assert not (tmp_path / "documents" / "AgeOfSteam" / "factions" / "omega").exists()


def _create(env, title, content="x"):  # noqa: F811
    return env.client.post(
        "/documents/create",
        json={"title": title, "content": content},
        headers=env.h("alice"),
    )


def test_a_document_is_read_back_for_editing(env, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    _create(env, "Règles du jeu", "Ligne 1\n\nLigne 2")
    r = env.client.get("/documents/faction/1/regles_du_jeu")
    assert r.status_code == 200
    assert r.json() == {"title": "Règles du jeu", "content": "Ligne 1\n\nLigne 2"}
    assert env.client.get("/documents/faction/1/absent").status_code == 404


def test_a_document_can_be_rewritten(env, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    _create(env, "Règles")
    r = env.client.put(
        "/documents/faction/1/regles",
        json={"title": "Règles", "content": "nouveau"},
        headers=env.h("alice"),
    )
    assert r.status_code == 200
    assert env.client.get("/documents/faction/1/regles").json()["content"] == "nouveau"
    folder = tmp_path / "documents" / "AgeOfSteam" / "factions" / "alpha"
    assert [p.name for p in folder.iterdir()] == ["regles.md"]  # no temp file left


def test_a_new_title_renames_the_document(env, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    _create(env, "Règles")
    _create(env, "Autre")
    h = env.h("alice")
    r = env.client.put(
        "/documents/faction/1/regles",
        json={"title": "Lois", "content": "x"},
        headers=h,
    )
    assert r.status_code == 200
    docs = env.client.get("/documents/faction/1").json()
    assert sorted(d["doc_name"] for d in docs) == ["autre", "lois"]
    # Taking a name that is used is refused, and nothing is lost
    r = env.client.put(
        "/documents/faction/1/lois",
        json={"title": "Autre", "content": "y"},
        headers=h,
    )
    assert r.status_code == 409
    assert env.client.get("/documents/faction/1/lois").status_code == 200


def test_a_document_can_be_deleted(env, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    _create(env, "Règles")
    r = env.client.delete("/documents/faction/1/regles", headers=env.h("alice"))
    assert r.status_code == 204
    assert env.client.get("/documents/faction/1").json() == []
    r = env.client.delete("/documents/faction/1/regles", headers=env.h("alice"))
    assert r.status_code == 404


def test_only_members_with_manage_docs_edit_documents(
    env, monkeypatch, tmp_path  # noqa: F811
):
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    _create(env, "Règles")
    body = {"title": "Règles", "content": "hacked"}
    # Not in the faction at all, and not logged in
    r = env.client.put(
        "/documents/faction/1/regles", json=body, headers=env.h("newbie")
    )
    assert r.status_code == 403
    r = env.client.delete("/documents/faction/1/regles", headers=env.h("newbie"))
    assert r.status_code == 403
    assert env.client.put("/documents/faction/1/regles", json=body).status_code == 401
    assert env.client.get("/documents/faction/1/regles").json()["content"] == "x"


def test_a_path_in_the_name_reaches_nothing_outside(
    env, monkeypatch, tmp_path  # noqa: F811
):
    monkeypatch.setattr(documentation, "DOCS_DIR", tmp_path / "documents")
    (tmp_path / "secret.md").write_text("secret")
    h = env.h("alice")
    for name in ("..%2F..%2Fsecret", "..%2F..%2F..%2Fsecret"):
        assert env.client.get(f"/documents/faction/1/{name}").status_code == 404
        assert (
            env.client.delete(f"/documents/faction/1/{name}", headers=h).status_code
            == 404
        )
    assert (tmp_path / "secret.md").read_text() == "secret"
