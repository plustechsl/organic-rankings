"""
Script de mantenimiento: reindexa todos los links existentes en OpenSearch.
Uso: docker exec organic_rankings_api python -m app.reindex_all
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.link import Link
from app.opensearch_client import index_link_document


def reindex_all(db: Session) -> int:
    links = db.scalars(select(Link)).all()
    count = 0

    for link in links:
        index_link_document(link)
        count += 1
        print(f"  + indexado: {link.title}")

    return count


if __name__ == "__main__":
    db = SessionLocal()
    try:
        total = reindex_all(db)
        print(f"\nListo. {total} links reindexados.")
    finally:
        db.close()
