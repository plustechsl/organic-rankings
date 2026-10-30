from sqlalchemy import text

from app.database import engine


def ensure_schema_updates() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE links "
                "ADD COLUMN IF NOT EXISTS sensitivity "
                "VARCHAR(20) NOT NULL DEFAULT 'none'"
            )
        )