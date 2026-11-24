import re
import unicodedata

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func, or_, select, text
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
FUZZY_SIMILARITY_THRESHOLD = 0.35


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    return "".join(
        char for char in value if not unicodedata.combining(char)
    )


def _haystack(link_translation=None, tag_names=None, category_label=None):
    # Solo campos del enlace: el título y la descripción de la lista no
    # deben hacer que aparezcan enlaces que no tienen que ver con la búsqueda.
    parts = [
        func.f_unaccent(func.lower(Link.title)),
        func.f_unaccent(func.lower(Link.description)),
    ]

    if category_label is not None:
        parts.append(category_label)

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

    if tag_names is not None:
        parts.append(func.coalesce(tag_names, ""))

    return func.concat_ws(" ", *parts)


def _levenshtein_condition(word: str, haystack):
    max_distance = 2 if len(word) >= 6 else 1

    tokens = func.regexp_split_to_table(
        haystack, r"[^[:alnum:]]+"
    ).table_valued("token").render_derived()

    return select(1).where(
        tokens.c.token != "",
        func.levenshtein_less_equal(
            word, tokens.c.token, max_distance
        ) <= max_distance,
    ).exists()


def _field_condition(word: str, field, allow_fuzzy: bool):
    """Misma coincidencia que la búsqueda general, pero sobre un solo campo.

    Se usa para decidir en qué nivel va cada enlace sin añadir columnas
    nuevas a la respuesta: la clasificación solo entra en el ORDER BY.
    """
    exact = field.op("~")(r"\m" + re.escape(word))

    if not allow_fuzzy or len(word) < FUZZY_MIN_WORD_LENGTH:
        return exact

    return or_(
        exact,
        func.strict_word_similarity(word, field)
        >= FUZZY_SIMILARITY_THRESHOLD,
        _levenshtein_condition(word, field),
    )


def ensure_search_ready() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch"))

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
    category_translation = aliased(Translation)
    tag_filter_translation = aliased(Translation)
    word_tag_relation = aliased(LinkTag)
    word_tag = aliased(Tag)
    word_tag_translation = aliased(Translation)
    word_category_translation = aliased(Translation)

    exact_conditions = []
    fuzzy_conditions = []
    filter_conditions = []
    fuzzy_enabled = False
    words = []

    # Los nombres de los tags entran en el texto buscable: así "economia"
    # (sin #) también encuentra los enlaces etiquetados con ese tag, y la
    # tolerancia a erratas existente cubre igualmente los tags.
    tag_label = func.coalesce(
        func.f_unaccent(func.lower(word_tag_translation.title)),
        func.f_unaccent(
            func.lower(func.replace(word_tag.name, "-", " "))
        ),
    )
    tag_names = (
        select(func.coalesce(func.string_agg(tag_label, " "), ""))
        .select_from(word_tag_relation)
        .join(word_tag, word_tag_relation.tag_id == word_tag.id)
        .outerjoin(
            word_tag_translation,
            and_(
                word_tag_translation.entity_type == "tag",
                word_tag_translation.entity_id == word_tag.id,
                word_tag_translation.lang == lang,
            ),
        )
        .where(word_tag_relation.link_id == Link.id)
        .correlate(Link)
        .scalar_subquery()
    )

    # El nombre de la categoría entra también en el texto buscable: antes
    # solo se podía acotar con el prefijo "categoria:".
    if lang:
        category_label = func.coalesce(
            func.f_unaccent(func.lower(word_category_translation.title)),
            func.f_unaccent(func.lower(category_alias.name)),
            "",
        )
    else:
        category_label = func.coalesce(
            func.f_unaccent(func.lower(category_alias.name)),
            "",
        )

    haystack = _haystack(
        link_translation if lang else None,
        tag_names,
        category_label,
    )

    if q:
        for raw_word in q.split():
            # "#economia" escrito directamente en la API equivale a
            # "economia"; la UI ya separa el # y lo envía como ?tag=.
            word = _normalize(raw_word.lstrip("#"))

            if not word:
                continue

            words.append(word)
            exact_conditions.append(
                _field_condition(word, haystack, allow_fuzzy=False)
            )
            fuzzy_conditions.append(
                _field_condition(word, haystack, allow_fuzzy=True)
            )

            if len(word) >= FUZZY_MIN_WORD_LENGTH:
                fuzzy_enabled = True

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
        filter_conditions.append(
            category_alias.id.in_(matching_categories)
        )

    if tag:
        normalized_tag = _normalize(tag)
        matching_tags = (
            select(Tag.id)
            .outerjoin(
                tag_filter_translation,
                and_(
                    tag_filter_translation.entity_type == "tag",
                    tag_filter_translation.entity_id == Tag.id,
                ),
            )
            .where(
                or_(
                    Tag.slug == slugify(tag),
                    func.f_unaccent(
                        func.lower(func.replace(Tag.name, "-", " "))
                    ) == normalized_tag,
                    func.f_unaccent(
                        func.lower(tag_filter_translation.title)
                    ) == normalized_tag,
                )
            )
        )
        filter_conditions.append(
            Link.id.in_(
                select(LinkTag.link_id).where(
                    LinkTag.tag_id.in_(matching_tags)
                )
            )
        )

    def build_query(word_conditions):
        query = (
            select(Link, LinkList, category_alias)
            .join(LinkList, Link.list_id == LinkList.id)
            .join(
                category_alias,
                LinkList.category_id == category_alias.id,
            )
            .where(*(word_conditions + filter_conditions))
        )

        if lang:
            query = query.outerjoin(
                link_translation,
                and_(
                    link_translation.entity_type == "link",
                    link_translation.entity_id == Link.id,
                    link_translation.lang == lang,
                ),
            ).outerjoin(
                word_category_translation,
                and_(
                    word_category_translation.entity_type == "category",
                    word_category_translation.entity_id == category_alias.id,
                    word_category_translation.lang == lang,
                ),
            )

        return query

    base_query = build_query(exact_conditions)

    total = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    )

    fuzzy_applied = False
    if total == 0 and fuzzy_enabled:
        base_query = build_query(fuzzy_conditions)
        fuzzy_applied = True

        total = db.scalar(
            select(func.count()).select_from(base_query.subquery())
        )

    # Clasificación interna: nivel 1 si coincide en el título del enlace,
    # la categoría o los tags; nivel 2 si la coincidencia está solo en el
    # título de la lista o en una descripción. Con varias palabras basta
    # una que coincida en nivel 1. El nivel no se devuelve: solo entra en
    # el ORDER BY, así que la API no cambia.
    if words:
        primary_fields = [
            func.coalesce(func.f_unaccent(func.lower(Link.title)), ""),
            category_label,
            tag_names,
        ]
        if lang:
            primary_fields.append(
                func.coalesce(
                    func.f_unaccent(func.lower(link_translation.title)),
                    "",
                )
            )

        primary_matches = [
            or_(
                *[
                    _field_condition(word, field, fuzzy_applied)
                    for field in primary_fields
                ]
            )
            for word in words
        ]
        relevance = case((or_(*primary_matches), 0), else_=1)
    else:
        relevance = None

    order_by = []
    if relevance is not None:
        order_by.append(relevance.asc())
    if sort == "recent":
        order_by.append(Link.created_at.desc())
    else:
        order_by.extend([Link.points.desc(), Link.created_at.desc()])

    base_query = base_query.order_by(*order_by)

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
