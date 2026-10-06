import os
import time

from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError


OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "opensearch")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))

LINKS_INDEX = "links"

client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    use_ssl=False,
    verify_certs=False,
)

LINKS_INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "spanish_analyzer": {
                    "type": "spanish",
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "spanish_analyzer",
            },
            "url": {
                "type": "keyword",
            },
            "description": {
                "type": "text",
                "analyzer": "spanish_analyzer",
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
                "analyzer": "spanish_analyzer",
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


def wait_for_opensearch(max_retries: int = 30, delay_seconds: float = 2.0) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            if client.ping():
                return
        except OpenSearchConnectionError:
            pass

        print(
            f"[opensearch] Not ready yet, retrying "
            f"({attempt}/{max_retries})..."
        )
        time.sleep(delay_seconds)

    raise RuntimeError(
        "Could not connect to OpenSearch after multiple retries"
    )


def ensure_links_index() -> None:
    wait_for_opensearch()

    if not client.indices.exists(index=LINKS_INDEX):
        client.indices.create(index=LINKS_INDEX, body=LINKS_INDEX_MAPPING)


def index_link_document(link) -> None:
    link_list = link.link_list
    category = link_list.category if link_list else None
    subcategory = link_list.subcategory if link_list else None

    tag_names = [
        relation.tag.name for relation in link.tag_relations
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


def delete_link_document(link_id: int) -> None:
    try:
        client.delete(index=LINKS_INDEX, id=str(link_id), refresh=True)
    except Exception:
        pass
