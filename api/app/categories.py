from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.config import TRANSLATION_LANGS
from app.database import get_db
from app.dependencies import require_admin
from app.models.category import Category
from app.models.link import Link
from app.models.link_tag import LinkTag
from app.models.list import LinkList
from app.models.tag import Tag
from app.models.translation import Translation
from app.models.user import User
from app.models.user_expertise import UserExpertise
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.translations import (
    delete_entity_translations,
    ensure_translations,
    get_lang,
)
from app.utils import slugify


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


def serialize_category(
    category: Category,
    tags: list[str],
    translation: Translation | None = None,
) -> dict:
    return {
        "id": category.id,
        "name": (
            translation.title
            if translation and translation.title
            else category.name
        ),
        "slug": category.slug,
        "tags": tags,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
    }


def get_tag_rows_by_category(db: Session) -> dict[int, list[Tag]]:
    rows = db.execute(
        select(LinkList.category_id, Tag)
        .join(Link, Link.list_id == LinkList.id)
        .join(LinkTag, LinkTag.link_id == Link.id)
        .join(Tag, LinkTag.tag_id == Tag.id)
        .distinct()
        .order_by(Tag.name)
    ).all()

    tags: dict[int, list[Tag]] = {}

    for category_id, tag in rows:
        tags.setdefault(category_id, []).append(tag)

    return tags


def get_tags_by_category(db: Session) -> dict[int, list[str]]:
    return {
        category_id: [tag.name for tag in tags]
        for category_id, tags in get_tag_rows_by_category(db).items()
    }


def _translated_tag_names(
    tags: list[Tag],
    translations: dict[int, Translation],
) -> list[str]:
    names = []

    for tag in tags:
        translation = translations.get(tag.id)
        names.append(
            translation.title
            if translation and translation.title
            else tag.name
        )

    return names


def _translate_category_payload(
    db: Session,
    categories: list[Category],
    tag_rows: dict[int, list[Tag]],
    lang: str,
) -> tuple[dict[int, Translation], dict[int, Translation]]:
    unique_tags: dict[int, Tag] = {}

    for tags in tag_rows.values():
        for tag in tags:
            unique_tags[tag.id] = tag

    category_translations = ensure_translations(
        db,
        "category",
        categories,
        lang,
        get_title=lambda category: category.name,
    )

    tag_translations = ensure_translations(
        db,
        "tag",
        list(unique_tags.values()),
        lang,
        get_title=lambda tag: tag.name,
    )

    return category_translations, tag_translations


@router.get("")
def list_categories(
    lang: str | None = Depends(get_lang),
    db: Session = Depends(get_db),
):
    categories = db.scalars(
        select(Category).order_by(Category.name)
    ).all()

    tag_rows = get_tag_rows_by_category(db)

    category_translations = {}
    tag_translations = {}

    if lang:
        category_translations, tag_translations = _translate_category_payload(
            db,
            categories,
            tag_rows,
            lang,
        )

    return [
        serialize_category(
            category,
            tags=_translated_tag_names(
                tag_rows.get(category.id, []),
                tag_translations,
            ),
            translation=category_translations.get(category.id),
        )
        for category in categories
    ]


@router.get("/{category_id}")
def get_category(
    category_id: int,
    lang: str | None = Depends(get_lang),
    db: Session = Depends(get_db),
):
    category = db.scalar(
        select(Category).where(Category.id == category_id)
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    tag_rows = get_tag_rows_by_category(db)

    category_translations = {}
    tag_translations = {}

    if lang:
        category_translations, tag_translations = _translate_category_payload(
            db,
            [category],
            tag_rows,
            lang,
        )

    return serialize_category(
        category,
        tags=_translated_tag_names(
            tag_rows.get(category.id, []),
            tag_translations,
        ),
        translation=category_translations.get(category.id),
    )


@router.post("", status_code=201)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    slug = slugify(payload.slug or payload.name)

    if not slug:
        raise HTTPException(
            status_code=400,
            detail="Could not generate a valid slug from the provided name",
        )

    existing = db.scalar(
        select(Category).where(Category.slug == slug)
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A category with this slug already exists",
        )

    category = Category(
        name=payload.name,
        slug=slug,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    _auto_translate_category(db, category)

    return serialize_category(category, tags=[])


def _auto_translate_category(db: Session, category: Category) -> None:
    from app.translate import translation_enabled

    if not translation_enabled():
        return

    for lang in TRANSLATION_LANGS:
        ensure_translations(
            db,
            "category",
            [category],
            lang,
            get_title=lambda c: c.name,
        )


@router.patch("/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category = db.scalar(
        select(Category).where(Category.id == category_id)
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    if payload.name is not None:
        category.name = payload.name

        db.execute(
            delete(Translation).where(
                Translation.entity_type == "category",
                Translation.entity_id == category.id,
            )
        )

    if payload.slug is not None:
        new_slug = slugify(payload.slug)

        if not new_slug:
            raise HTTPException(
                status_code=400,
                detail="Could not generate a valid slug",
            )

        if new_slug != category.slug:
            existing = db.scalar(
                select(Category).where(Category.slug == new_slug)
            )

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="A category with this slug already exists",
                )

            category.slug = new_slug

    db.commit()
    db.refresh(category)

    return serialize_category(
        category,
        tags=get_tags_by_category(db).get(category.id, []),
    )


FALLBACK_CATEGORY_NAMES = ("Varios", "Cat varios")


def get_or_create_fallback_category(db: Session) -> Category:
    fallback = db.scalar(
        select(Category).where(
            or_(
                Category.name.ilike("Varios"),
                Category.name.ilike("Cat varios"),
            )
        )
    )

    if fallback:
        return fallback

    fallback = db.scalar(
        select(Category).where(Category.slug == "varios")
    )

    if fallback:
        return fallback

    fallback = Category(name="Varios", slug="varios")
    db.add(fallback)
    db.flush()

    return fallback


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category = db.scalar(
        select(Category).where(Category.id == category_id)
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    is_fallback = category.name.strip().lower() in {
        name.lower() for name in FALLBACK_CATEGORY_NAMES
    }

    main_lists = db.scalars(
        select(LinkList).where(LinkList.category_id == category_id)
    ).all()

    fallback = None

    if main_lists:
        if is_fallback:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot delete the fallback category while lists use it"
                ),
            )

        fallback = get_or_create_fallback_category(db)

        if fallback.id == category_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot delete the fallback category while lists use it"
                ),
            )

        for link_list in main_lists:
            link_list.category_id = fallback.id

    db.execute(
        delete(UserExpertise).where(UserExpertise.category_id == category_id)
    )

    delete_entity_translations(db, "category", category_id)

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted",
        "id": category_id,
        "moved_lists_to": fallback.id if fallback else None,
    }
