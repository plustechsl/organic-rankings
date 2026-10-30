import unicodedata

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, aliased

from app.database import engine, get_db
from app.models.category import Category
from app.models.link import Link
from app.models.link_tag import LinkTag
from app.models.list import LinkList
from app.models.tag import Tag
from app.utils import slugify


FUZZY_MIN_WORD_LENGTH = 5
FUZZY_SIMILARITY_THRESHOLD = 0.4


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    return "".join(
        char for char in value if not unicodedata.combining(char)
    )


def _haystack():
    return func.concat_ws(
        " ",
        func.f_unaccent(func.lower(Link.title)),
        func.f_unaccent(func.lower(Link.description)),
        func.f_unaccent(func.lower(LinkList.title)),
    )


def ensure_search_ready() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

        conn.execute(
            text(
                "CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text "
                "LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT "
                "AS $$ SELECT public.unaccent("
                "'public.unaccent'::regdictionary, $1) $$"
            )
        )

        for column in ("title", "description"):
            conn.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_links_{column}_trgm "
                    f"ON links USING gin "
                    f"(f_unaccent(lower({column})) gin_trgm_ops)"
                )
            )

        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lists_title_trgm "
                "ON lists USING gin "
                "(f_unaccent(lower(title)) gin_trgm_ops)"
            )
        )


@router.get("")
def search(
    q: str | None = Query(
        default=None,
        description="Texto que se quiere buscar",
    ),
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    sort: str = Query(
        default="points",
        pattern="^(points|recent)$",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    category_alias = aliased(Category)

    conditions = []

    if q:
        haystack = _haystack()

        for raw_word in q.split():
            word = _normalize(raw_word)

            if not word:
                continue

            escaped = (
                word.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )

            condition = haystack.like(f"%{escaped}%", escape="\\")

            if len(word) >= FUZZY_MIN_WORD_LENGTH:
                condition = or_(
                    condition,
                    func.word_similarity(word, haystack)
                    >= FUZZY_SIMILARITY_THRESHOLD,
                )

            conditions.append(condition)

    if category:
        normalized = _normalize(category)
        conditions.append(
            func.f_unaccent(func.lower(category_alias.name))
            == normalized
        )

    base_query = (
        select(Link, LinkList, category_alias)
        .join(LinkList, Link.list_id == LinkList.id)
        .join(
            category_alias,
            LinkList.category_id == category_alias.id,
        )
        .where(*conditions)
    )

    if tag:
        base_query = (
            base_query.join(LinkTag, LinkTag.link_id == Link.id)
            .join(Tag, LinkTag.tag_id == Tag.id)
            .where(Tag.slug == slugify(tag))
        )

    total = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    )

    if sort == "recent":
        base_query = base_query.order_by(Link.created_at.desc())
    else:
        base_query = base_query.order_by(
            Link.points.desc(),
            Link.created_at.desc(),
        )

    rows = db.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    ).all()

    tags_by_link: dict[int, list[str]] = {}
    link_ids = [link.id for link, *_ in rows]

    if link_ids:
        tag_rows = db.execute(
            select(LinkTag.link_id, Tag.name)
            .join(Tag, LinkTag.tag_id == Tag.id)
            .where(LinkTag.link_id.in_(link_ids))
            .order_by(Tag.name)
        )

        for link_id, tag_name in tag_rows:
            tags_by_link.setdefault(link_id, []).append(tag_name)

    results = [
        {
            "id": link.id,
            "title": link.title,
            "url": link.url,
            "description": link.description,
            "points": link.points,
            "created_at": link.created_at,
            "list_id": link_list.id,
            "list_title": link_list.title,
            "category_id": category.id if category else None,
            "category_name": category.name if category else None,
            "tags": tags_by_link.get(link.id, []),
        }
        for link, link_list, category in rows
    ]

    return {
        "query": q,
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": results,
    }
