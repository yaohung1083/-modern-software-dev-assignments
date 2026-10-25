from datetime import datetime, timedelta

import pytest
from backend.app.indexes import ensure_query_indexes
from backend.app.models import Base, Note
from backend.app.routers.notes import search_notes
from sqlalchemy import create_engine, insert, select, text
from sqlalchemy.orm import Session


@pytest.fixture()
def populated_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'indexes.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            insert(Note),
            [
                {
                    "id": i + 1,
                    "title": f"Title {(i * 37) % 101:03d}",
                    "content": "MATCH body" if i % 3 == 0 else "other",
                    "created_at": datetime(2020, 1, 1) + timedelta(seconds=i % 71),
                }
                for i in range(5000)
            ],
        )
    yield engine
    engine.dispose()


@pytest.mark.parametrize(
    ("sort", "ordering", "index_name"),
    [
        ("title_asc", (Note.title.asc(), Note.id.asc()), "ix_notes_title_id"),
        (
            "created_desc",
            (Note.created_at.desc(), Note.id.desc()),
            "ix_notes_created_at_id",
        ),
    ],
)
def test_index_removes_sort_and_preserves_search(populated_engine, sort, ordering, index_name):
    engine = populated_engine
    statement = select(Note).order_by(*ordering).offset(100).limit(10)
    sql = str(statement.compile(engine, compile_kwargs={"literal_binds": True}))

    def plan():
        with engine.connect() as connection:
            return " ".join(row[3] for row in connection.execute(text("EXPLAIN QUERY PLAN " + sql)))

    def results():
        with Session(engine) as session:
            return [
                search_notes(q=q, page=page, page_size=10, sort=sort, db=session).model_dump()
                for q in [None, "mAtCh", "missing", "%"]
                for page in [1, 11, 501]
            ]

    before = results()
    assert "TEMP B-TREE FOR ORDER BY" in plan()
    ensure_query_indexes(engine)
    ensure_query_indexes(engine)  # Startup is idempotent.
    after_plan = plan()
    assert index_name in after_plan
    assert "TEMP B-TREE FOR ORDER BY" not in after_plan
    assert results() == before
    assert before[0]["total"] == 5000
    assert before[3]["total"] == 1667


def test_application_startup_installs_indexes(client):
    from backend.app import main

    with main.engine.connect() as connection:
        names = {row[1] for row in connection.execute(text("PRAGMA index_list(notes)"))}
    assert {"ix_notes_title_id", "ix_notes_created_at_id"} <= names
