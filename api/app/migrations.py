from sqlalchemy import text

from app.database import engine


COLUMNS = (
    (
        "links",
        "sensitivity",
        "VARCHAR(20) NOT NULL DEFAULT 'none'",
    ),
    (
        "links",
        "ai_score",
        "INTEGER",
    ),
    (
        "links",
        "ai_checked_at",
        "TIMESTAMP",
    ),
)


def ensure_schema_updates() -> None:
    with engine.begin() as conn:
        for table, column, definition in COLUMNS:
            conn.execute(
                text(
                    f"ALTER TABLE {table} "
                    f"ADD COLUMN IF NOT EXISTS {column} {definition}"
                )
            )
