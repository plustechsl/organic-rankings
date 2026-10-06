from fastapi import APIRouter, Query

from app.opensearch_client import LINKS_INDEX, client


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get("")
def search(
    q: str | None = Query(
        default=None,
        description="Texto que se quiere buscar",
    ),
    category: str | None = Query(default=None),
    subcategory: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    sort: str = Query(
        default="points",
        pattern="^(points|recent)$",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    must_clauses = []
    filter_clauses = []

    if q:
        must_clauses.append(
            {
                "multi_match": {
                    "query": q,
                    "fields": [
                        "title^3",
                        "description",
                        "list_title^2",
                    ],
                }
            }
        )

    if category:
        filter_clauses.append({"term": {"category_name": category}})

    if subcategory:
        filter_clauses.append({"term": {"subcategory_name": subcategory}})

    if tag:
        filter_clauses.append({"term": {"tags": tag}})

    if must_clauses or filter_clauses:
        query_body = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
            }
        }
    else:
        query_body = {"match_all": {}}

    sort_body = (
        [{"points": {"order": "desc"}}]
        if sort == "points"
        else [{"created_at": {"order": "desc"}}]
    )

    response = client.search(
        index=LINKS_INDEX,
        body={
            "query": query_body,
            "sort": sort_body,
            "from": (page - 1) * page_size,
            "size": page_size,
        },
    )

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    results = [
        {
            "id": int(hit["_id"]),
            **hit["_source"],
        }
        for hit in hits
    ]

    return {
        "query": q,
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": results,
    }
