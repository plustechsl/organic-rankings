import time

from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError

from app.config import (
    LINKS_INDEX,
    OPENSEARCH_HOST,
    OPENSEARCH_PORT,
)

client = OpenSearch(
    hosts=[
        {
            "host": OPENSEARCH_HOST,
            "port": OPENSEARCH_PORT,
        }
    ],
    use_ssl=False,
    verify_certs=False,
)

LINKS_INDEX_MAPPING_VERSION = 2

LINKS_INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "filter": {
                "spanish_stop": {
                    "type": "stop",
                    "stopwords": "_spanish_",
                },
                "spanish_stemmer": {
                    "type": "stemmer",
                    "language": "light_spanish",
                },
            },
            "analyzer": {
                "spanish_folding": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "asciifolding",
                        "lowercase",
                        "spanish_stop",
                        "spanish_stemmer",
                    ],
                }
            }
        }
    },
    "mappings": {
        "_meta": {
            "mapping_version": LINKS_INDEX_MAPPING_VERSION,
        },
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "spanish_folding",
            },
            "url": {
                "type": "keyword",
            },
            "description": {
                "type": "text",
                "analyzer": "spanish_folding",
            },
            "points": {
                "type": "integer",
            },
            "created_at": {
                "type": "date",
            },
            "list_id": {
                "type": "integer",
            },
            "list_title": {
                "type": "text",
                "analyzer": "spanish_folding",
            },
            "category_id": {
                "type": "integer",
            },
            "category_name": {
                "type": "keyword",
            },
            "subcategory_id": {
                "type": "integer",
            },
            "subcategory_name": {
                "type": "keyword",
            },
            "tags": {
                "type": "keyword",
            },
        }
    },
}


def wait_for_opensearch(max_retries: int = 30, delay_seconds: float = 2.0):
    for attempt in range(1, max_retries + 1):
        try:
            if client.ping():
                return
        except OpenSearchConnectionError:
            pass

        print(
            f"[opensearch] Not ready yet ({attempt}/{max_retries})..."
        )
        time.sleep(delay_seconds)

    raise RuntimeError("Could not connect to OpenSearch")


def _existing_mapping_version():
    mapping = client.indices.get_mapping(index=LINKS_INDEX)

    return (
        mapping.get(LINKS_INDEX, {})
        .get("mappings", {})
        .get("_meta", {})
        .get("mapping_version")
    )


def _reindex_all_links():
    from app.database import SessionLocal
    from app.reindex_all import reindex_all

    db = SessionLocal()
    try:
        total = reindex_all(db)
        print(f"[opensearch] Índice recreado y reindexado: {total} links.")
    finally:
        db.close()


def ensure_links_index():
    wait_for_opensearch()

    if client.indices.exists(index=LINKS_INDEX):
        if _existing_mapping_version() == LINKS_INDEX_MAPPING_VERSION:
            return

        client.indices.delete(index=LINKS_INDEX)

    client.indices.create(
        index=LINKS_INDEX,
        body=LINKS_INDEX_MAPPING,
    )

    _reindex_all_links()


def index_link_document(link):
    link_list = link.link_list
    category = link_list.category if link_list else None
    subcategory = link_list.subcategory if link_list else None

    tag_names = [
        relation.tag.name
        for relation in link.tag_relations
    ]

    document = {
        "title": link.title,
        "url": link.url,
        "description": link.description or "",
        "points": link.points,
        "created_at": link.created_at.isoformat(),
        "list_id": link.list_id,
        "list_title": link_list.title if link_list else None,
        "category_id": category.id if category else None,
        "category_name": category.name if category else None,
        "subcategory_id": subcategory.id if subcategory else None,
        "subcategory_name": subcategory.name if subcategory else None,
        "tags": tag_names,
    }

    client.index(
        index=LINKS_INDEX,
        id=str(link.id),
        body=document,
        refresh=True,
    )


def delete_link_document(link_id: int):
    try:
        client.delete(
            index=LINKS_INDEX,
            id=str(link_id),
            refresh=True,
        )
    except Exception:
        pass