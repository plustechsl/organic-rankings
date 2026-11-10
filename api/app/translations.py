import logging

from fastapi import Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import TRANSLATION_LANGS
from app.models.translation import Translation
from app.translate import translate_texts


logger = logging.getLogger("uvicorn.error")


def normalize_lang(lang: str | None) -> str | None:
    if not lang:
        return None

    value = lang.strip().lower().split("-")[0]

    if value not in TRANSLATION_LANGS:
        return None

    return value


def get_lang(
    lang: str | None = Query(
        default=None,
        description="Idioma de las traducciones (en, ca)",
    ),
) -> str | None:
    return normalize_lang(lang)


def get_translations(
    db: Session,
    entity_type: str,
    entity_ids: list[int],
    lang: str,
) -> dict[int, Translation]:
    if not entity_ids:
        return {}

    rows = db.scalars(
        select(Translation).where(
            Translation.entity_type == entity_type,
            Translation.entity_id.in_(entity_ids),
            Translation.lang == lang,
        )
    ).all()

    return {row.entity_id: row for row in rows}


def _is_complete(translation: Translation | None, description: str | None) -> bool:
    if translation is None:
        return False

    if not translation.title:
        return False

    if description and not translation.description:
        return False

    return True


def ensure_translations(
    db: Session,
    entity_type: str,
    items: list,
    lang: str,
    get_title,
    get_description=None,
) -> dict[int, Translation]:
    """Traduce en lote y devuelve {entity_id: Translation}.

    Fallo-abierto: si el proveedor falla, devuelve las traducciones
    que existan en BD (o vacío) y el llamador muestra el original.
    """
    by_id = get_translations(
        db,
        entity_type,
        [item.id for item in items],
        lang,
    )

    pending = [
        item
        for item in items
        if not _is_complete(
            by_id.get(item.id),
            get_description(item) if get_description else None,
        )
    ]

    if not pending:
        return by_id

    texts: list[str] = []

    for item in pending:
        texts.append(get_title(item))

        if get_description:
            description = get_description(item)

            if description:
                texts.append(description)

    translated = translate_texts(texts, lang)

    if translated is None or len(translated) != len(texts):
        return by_id

    index = 0

    for item in pending:
        new_title = translated[index]
        index += 1

        new_description = None

        if get_description:
            description = get_description(item)

            if description:
                new_description = translated[index]
                index += 1

        if not new_title:
            continue

        row = by_id.get(item.id)

        if row:
            row.title = new_title
            row.description = new_description
        else:
            row = Translation(
                entity_type=entity_type,
                entity_id=item.id,
                lang=lang,
                title=new_title,
                description=new_description,
            )
            db.add(row)
            by_id[item.id] = row

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.warning("Could not persist translations for %s", entity_type)
        return get_translations(
            db,
            entity_type,
            [item.id for item in items],
            lang,
        )

    return by_id


def delete_entity_translations(
    db: Session,
    entity_type: str,
    entity_id: int,
) -> None:
    db.execute(
        delete(Translation).where(
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
        )
    )


def backfill_all(db: Session) -> dict[str, int]:
    """Traduce el contenido existente a todos los idiomas (arranque)."""
    from app.models.category import Category
    from app.models.link import Link
    from app.models.list import LinkList
    from app.models.tag import Tag

    report = {}

    for lang in TRANSLATION_LANGS:
        counts = {}

        categories = db.scalars(select(Category)).all()
        ensure_translations(
            db,
            "category",
            categories,
            lang,
            get_title=lambda c: c.name,
        )
        counts["categories"] = len(categories)

        tags = db.scalars(select(Tag)).all()
        ensure_translations(
            db,
            "tag",
            tags,
            lang,
            get_title=lambda t: t.name,
        )
        counts["tags"] = len(tags)

        lists = db.scalars(select(LinkList)).all()
        ensure_translations(
            db,
            "list",
            lists,
            lang,
            get_title=lambda l: l.title,
            get_description=lambda l: l.description,
        )
        counts["lists"] = len(lists)

        links = db.scalars(select(Link)).all()
        ensure_translations(
            db,
            "link",
            links,
            lang,
            get_title=lambda l: l.title,
            get_description=lambda l: l.description,
        )
        counts["links"] = len(links)

        report[lang] = counts

    return report
