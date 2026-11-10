from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.config import TRANSLATION_LANGS
from app.database import get_db
from app.dependencies import get_current_user
from app.ratelimit import limit_creation
from app.models.category import Category
from app.models.list import LinkList
from app.models.translation import Translation
from app.models.user import User
from app.schemas.list import ListCreate, ListUpdate
from app.translations import (
    delete_entity_translations,
    ensure_translations,
    get_lang,
)
from app.utils import slugify


router = APIRouter(
    prefix="/lists",
    tags=["Lists"],
)


def serialize_list(
    link_list: LinkList,
    translation: Translation | None = None,
) -> dict:
    return {
        "id": link_list.id,
        "user_id": link_list.user_id,
        "username": link_list.user.username if link_list.user else None,
        "title": (
            translation.title
            if translation and translation.title
            else link_list.title
        ),
        "slug": link_list.slug,
        "description": (
            translation.description
            if translation and translation.description
            else link_list.description
        ),
        "image_url": link_list.image_url,
        "points": sum(link.points for link in link_list.links),
        "category_id": link_list.category_id,
        "created_at": link_list.created_at,
        "updated_at": link_list.updated_at,
    }


def get_owned_list_or_403(
    list_id: int,
    current_user: User,
    db: Session,
) -> LinkList:
    link_list = db.scalar(
        select(LinkList).where(LinkList.id == list_id)
    )

    if not link_list:
        raise HTTPException(
            status_code=404,
            detail="List not found",
        )

    is_owner = link_list.user_id == current_user.id
    is_privileged = current_user.role in {"admin", "moderator"}

    if not is_owner and not is_privileged:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to modify this list",
        )

    return link_list


def validate_category(
    category_id: int,
    db: Session,
) -> None:
    category = db.scalar(
        select(Category).where(Category.id == category_id)
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )


@router.get("")
def list_lists(
    slug: str | None = None,
    lang: str | None = Depends(get_lang),
    db: Session = Depends(get_db),
):
    query = (
        select(LinkList)
        .options(joinedload(LinkList.user), selectinload(LinkList.links))
        .order_by(LinkList.created_at.desc())
    )

    if slug:
        query = query.where(LinkList.slug == slug)

    lists = db.scalars(query).all()

    translations = {}

    if lang:
        translations = ensure_translations(
            db,
            "list",
            lists,
            lang,
            get_title=lambda link_list: link_list.title,
            get_description=lambda link_list: link_list.description,
        )

    return [
        serialize_list(
            link_list,
            translation=translations.get(link_list.id),
        )
        for link_list in lists
    ]


@router.get("/{list_id}")
def get_list(
    list_id: int,
    lang: str | None = Depends(get_lang),
    db: Session = Depends(get_db),
):
    link_list = db.scalar(
        select(LinkList)
        .options(joinedload(LinkList.user), selectinload(LinkList.links))
        .where(LinkList.id == list_id)
    )

    if not link_list:
        raise HTTPException(
            status_code=404,
            detail="List not found",
        )

    translation = None

    if lang:
        translations = ensure_translations(
            db,
            "list",
            [link_list],
            lang,
            get_title=lambda l: l.title,
            get_description=lambda l: l.description,
        )
        translation = translations.get(link_list.id)

    return serialize_list(link_list, translation=translation)


@router.post("", status_code=201)
def create_list(
    payload: ListCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit_creation(request, current_user.id)

    validate_category(payload.category_id, db)

    slug = slugify(payload.slug or payload.title)

    if not slug:
        raise HTTPException(
            status_code=400,
            detail="Could not generate a valid slug from the provided title",
        )

    existing = db.scalar(
        select(LinkList).where(LinkList.slug == slug)
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A list with this slug already exists",
        )

    link_list = LinkList(
        user_id=current_user.id,
        category_id=payload.category_id,
        title=payload.title,
        slug=slug,
        description=payload.description,
        image_url=payload.image_url,
    )

    db.add(link_list)
    db.commit()
    db.refresh(link_list)

    _auto_translate_list(db, link_list)

    return serialize_list(link_list)


def _auto_translate_list(db: Session, link_list: LinkList) -> None:
    from app.translate import translation_enabled

    if not translation_enabled():
        return

    for lang in TRANSLATION_LANGS:
        ensure_translations(
            db,
            "list",
            [link_list],
            lang,
            get_title=lambda l: l.title,
            get_description=lambda l: l.description,
        )


@router.patch("/{list_id}")
def update_list(
    list_id: int,
    payload: ListUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link_list = get_owned_list_or_403(list_id, current_user, db)

    if payload.category_id is not None:
        validate_category(payload.category_id, db)

        link_list.category_id = payload.category_id

    if payload.title is not None:
        link_list.title = payload.title

    if payload.slug is not None:
        new_slug = slugify(payload.slug)

        if not new_slug:
            raise HTTPException(
                status_code=400,
                detail="Could not generate a valid slug",
            )

        if new_slug != link_list.slug:
            existing = db.scalar(
                select(LinkList).where(LinkList.slug == new_slug)
            )

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="A list with this slug already exists",
                )

            link_list.slug = new_slug

    if payload.description is not None:
        link_list.description = payload.description

    if payload.image_url is not None:
        link_list.image_url = payload.image_url

    if payload.title is not None or payload.description is not None:
        db.execute(
            delete(Translation).where(
                Translation.entity_type == "list",
                Translation.entity_id == link_list.id,
            )
        )

    db.commit()
    db.refresh(link_list)

    return serialize_list(link_list)


@router.delete("/{list_id}")
def delete_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link_list = get_owned_list_or_403(list_id, current_user, db)

    delete_entity_translations(db, "list", link_list.id)

    db.delete(link_list)
    db.commit()

    return {
        "message": "List deleted",
        "id": list_id,
    }
