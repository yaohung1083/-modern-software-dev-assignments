from datetime import datetime

import pytest
from backend.app import main
from backend.app.db import migrate_notes_created_at
from backend.app.models import Note
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session


def test_create_and_list_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/search/")
    assert r.status_code == 200

    r = client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1


def create_note(client, title, content="body"):
    response = client.post("/notes/", json={"title": title, "content": content})
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize("q", [None, "", "hELLo", "WORLD", "missing"])
def test_search_matching(client, q):
    note = create_note(client, "Hello", "World")
    create_note(client, "Other", "Unrelated")
    response = client.get("/notes/search/", params={} if q is None else {"q": q})
    assert response.status_code == 200
    data = response.json()
    expected = 2 if not q else (0 if q == "missing" else 1)
    assert data["total"] == len(data["items"]) == expected
    assert data["page"] == 1
    assert data["page_size"] == 10
    if q and q != "missing":
        assert data["items"] == [note]


@pytest.mark.parametrize("q", ["%", "_", "\\"])
def test_search_treats_wildcards_as_literal_text(client, q):
    note = create_note(client, f"Literal {q}")
    create_note(client, "Other")
    data = client.get("/notes/search/", params={"q": q}).json()
    assert data["total"] == 1
    assert data["items"] == [note]


def test_filtered_pagination_and_title_sort(client):
    notes = [create_note(client, title, "match") for title in ["C", "A", "B"]]
    create_note(client, "Excluded", "other")
    for page, expected in [(1, [notes[1], notes[2]]), (2, [notes[0]]), (3, [])]:
        response = client.get(
            "/notes/search/",
            params={
                "q": "MATCH",
                "sort": "title_asc",
                "page": page,
                "page_size": 2,
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "items": expected,
            "total": 3,
            "page": page,
            "page_size": 2,
        }


def test_created_sort_uses_timestamp_and_id_tiebreaker(client):
    notes = [create_note(client, "Same") for _ in range(3)]
    with main.engine.begin() as connection:
        connection.execute(text("UPDATE notes SET created_at = '2020-01-01 00:00:00'"))
        connection.execute(
            text("UPDATE notes SET created_at = '2021-01-01 00:00:00' WHERE id = :id"),
            {"id": notes[0]["id"]},
        )
    expected = [notes[0], notes[2], notes[1]]
    for params in [{}, {"sort": "created_desc"}]:
        assert client.get("/notes/search/", params=params).json()["items"] == expected
    assert client.get("/notes/search/", params={"sort": "title_asc"}).json()["items"] == notes


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": -1},
        {"page": "abc"},
        {"page": "1.5"},
        {"page_size": 0},
        {"page_size": -1},
        {"page_size": 101},
        {"page_size": "abc"},
        {"sort": "unknown"},
    ],
)
def test_search_invalid_parameters(client, params):
    assert client.get("/notes/search/", params=params).status_code == 422


def test_empty_search_and_maximum_page_size(client):
    response = client.get("/notes/search/", params={"page_size": 100})
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 100}


def test_search_paginates_in_sql(client):
    for index in range(12):
        create_note(client, f"Note {index}")
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.upper())

    event.listen(main.engine, "before_cursor_execute", capture)
    try:
        data = client.get("/notes/search/", params={"page": 2}).json()
    finally:
        event.remove(main.engine, "before_cursor_execute", capture)
    assert data["total"] == 12
    assert len(data["items"]) == 2
    row_queries = [sql for sql in statements if sql.startswith("SELECT") and "COUNT(" not in sql]
    assert len(row_queries) == 1
    assert "LIMIT" in row_queries[0] and "OFFSET" in row_queries[0]


def test_legacy_database_migration_preserves_notes(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL)"
                )
            )
            connection.execute(text("INSERT INTO notes VALUES (1, 'Legacy', 'Keep this')"))
        migrate_notes_created_at(engine)
        migrate_notes_created_at(engine)
        with Session(engine) as session:
            legacy = session.get(Note, 1)
            assert (legacy.title, legacy.content) == ("Legacy", "Keep this")
            assert legacy.created_at == datetime(1970, 1, 1)
            new = Note(title="New", content="Works")
            session.add(new)
            session.commit()
            assert new.created_at > legacy.created_at
            assert (
                session.scalars(select(Note).order_by(Note.created_at.desc())).first().id == new.id
            )
    finally:
        engine.dispose()


def test_get_note_and_missing_note(client):
    note = create_note(client, "Fetch me")
    assert client.get(f"/notes/{note['id']}").json() == note
    assert client.get("/notes/999999").status_code == 404
