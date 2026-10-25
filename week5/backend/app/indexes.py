"""Indexes for the two supported notes search orderings."""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def ensure_query_indexes(engine: Engine) -> None:
    """Run after table creation / legacy migration; safe on every startup.

    These indexes avoid temporary sorting for paginated searches. They do not
    accelerate arbitrary substring matching in title/content.
    """
    with engine.begin() as connection:
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_notes_title_id ON notes (title, id)")
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_notes_created_at_id "
                "ON notes (created_at DESC, id DESC)"
            )
        )
