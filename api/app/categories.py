from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.category import Category
from app.models.link import Link
from app.models.link_tag import LinkTag
from app.models.list import LinkList
from app.models.tag import Tag
from app.models.user import User
from app.models.user_expertise import UserExpertise
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils import slugify


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


def serialize_category(category: Category, tags: list[str]) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "tags": tags,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
    }


def get_tags_by_category(db: Session) -> dict[int, list[str]]:
    rows = db.execute(
        select(LinkList.category_id, Tag.name)
        .join(Link, Link.list_id == LinkList.id)
        .join(LinkTag, LinkTag.link_id == Link.id)
        .join(Tag, LinkTag.tag_id == Tag.id)
        .distinct()
        .order_by(Tag.name)
    ).all()

    tags: dict[int, list[str]] = {}

    for category_id, name in rows:
        tags.setdefault(category_id, []).append(name)

    return tags


@router.get("")
def list_categories(
    db: Session = Depends(get_db),
):
    categories = db.scalars(
        select(Category).order_by(Category.name)
    ).all()

    tags_by_category = get_tags_by_category(db)

    return [
        serialize_category(
            category,
            tags=tags_by_category.get(category.id, []),
        )
        for category in categories
    ]


@router.get("/{category_id}")
def get_category(
    category_id: int,
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

    return serialize_category(
        category,
        tags=get_tags_by_category(db).get(category.id, []),
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

    return serialize_category(category, tags=[])


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

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted",
        "id": category_id,
        "moved_lists_to": fallback.id if fallback else None,
    }
