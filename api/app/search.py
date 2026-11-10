import unicodedata

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.orm import Session, aliased

from app.config import TRANSLATION_LANGS
from app.database import engine, get_db
from app.models.category import Category
from app.models.link import Link
from app.models.link_tag import LinkTag
from app.models.list import LinkList
from app.models.tag import Tag
from app.models.translation import Translation
from app.translations import ensure_translations, get_lang
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


def _haystack(link_translation=None, list_translation=None):
    parts = [
        func.f_unaccent(func.lower(Link.title)),
        func.f_unaccent(func.lower(Link.description)),
        func.f_unaccent(func.lower(LinkList.title)),
    ]

    if link_translation is not None:
        parts.append(
            func.coalesce(
                func.f_unaccent(func.lower(link_translation.title)),
                "",
            )
        )
        parts.append(
            func.coalesce(
                func.f_unaccent(func.lower(link_translation.description)),
                "",
            )
        )

    if list_translation is not None:
        parts.append(
            func.coalesce(
                func.f_unaccent(func.lower(list_translation.title)),
                "",
            )
        )
        parts.append(
            func.coalesce(
                func.f_unaccent(func.lower(list_translation.description)),
                "",
            )
        )

    return func.concat_ws(" ", *parts)


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
    lang: str | None = Depends(get_lang),
    db: Session = Depends(get_db),
):
    category_alias = aliased(Category)
    link_translation = aliased(Translation)
    list_translation = aliased(Translation)
    category_translation = aliased(Translation)

    conditions = []

    haystack = _haystack(
        link_translation if lang else None,
        list_translation if lang else None,
    )

    if q:
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
        matching_categories = (
            select(Category.id)
            .outerjoin(
                category_translation,
                and_(
                    category_translation.entity_type == "category",
                    category_translation.entity_id == Category.id,
                ),
            )
            .where(
                or_(
                    func.f_unaccent(func.lower(Category.name))
                    == normalized,
                    func.f_unaccent(
                        func.lower(category_translation.title)
                    )
                    == normalized,
                )
            )
        )
        conditions.append(
            category_alias.id.in_(matching_categories)
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

    if lang:
        base_query = base_query.outerjoin(
            link_translation,
            and_(
                link_translation.entity_type == "link",
                link_translation.entity_id == Link.id,
                link_translation.lang == lang,
            ),
        ).outerjoin(
            list_translation,
            and_(
                list_translation.entity_type == "list",
                list_translation.entity_id == LinkList.id,
                list_translation.lang == lang,
            ),
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

    links = [link for link, *_ in rows]
    categories = list(
        {
            category.id: category
            for _, _, category in rows
            if category
        }.values()
    )

    link_translations = {}
    category_translations = {}

    if lang and (links or categories):
        link_translations = ensure_translations(
            db,
            "link",
            links,
            lang,
            get_title=lambda link: link.title,
            get_description=lambda link: link.description,
        )
        category_translations = ensure_translations(
            db,
            "category",
            categories,
            lang,
            get_title=lambda category: category.name,
        )

    tags_by_link: dict[int, list[str]] = {}
    tag_translations = {}
    link_ids = [link.id for link in links]

    if link_ids:
        tag_rows = db.execute(
            select(LinkTag.link_id, Tag)
            .join(Tag, LinkTag.tag_id == Tag.id)
            .where(LinkTag.link_id.in_(link_ids))
            .order_by(Tag.name)
        )

        grouped: dict[int, list[Tag]] = {}

        for link_id, tag in tag_rows:
            grouped.setdefault(link_id, []).append(tag)

        if lang:
            unique_tags = {
                tag.id: tag
                for tags in grouped.values()
                for tag in tags
            }

            tag_translations = ensure_translations(
                db,
                "tag",
                list(unique_tags.values()),
                lang,
                get_title=lambda tag: tag.name,
            )

            tags_by_link = {
                link_id: [
                    tag_translations[tag.id].title
                    if tag.id in tag_translations
                    and tag_translations[tag.id].title
                    else tag.name
                    for tag in tags
                ]
                for link_id, tags in grouped.items()
            }
        else:
            tags_by_link = {
                link_id: [tag.name for tag in tags]
                for link_id, tags in grouped.items()
            }

    results = [
        {
            "id": link.id,
            "title": (
                link_translations[link.id].title
                if lang
                and link.id in link_translations
                and link_translations[link.id].title
                else link.title
            ),
            "url": link.url,
            "description": (
                link_translations[link.id].description
                if lang
                and link.id in link_translations
                and link_translations[link.id].description
                else link.description
            ),
            "points": link.points,
            "sensitivity": link.sensitivity,
            "created_at": link.created_at,
            "list_id": link_list.id,
            "list_title": link_list.title,
            "category_id": category.id if category else None,
            "category_name": (
                category_translations[category.id].title
                if lang
                and category
                and category.id in category_translations
                and category_translations[category.id].title
                else category.name if category else None
            ),
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
