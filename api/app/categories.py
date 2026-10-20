from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.category import Category
from app.models.list import LinkList
from app.models.user import User
from app.models.user_expertise import UserExpertise
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils import slugify


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


def serialize_category(category: Category, include_children: bool = False) -> dict:
    data = {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "parent_id": category.parent_id,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
    }

    if include_children:
        data["children"] = [
            serialize_category(child, include_children=True)
            for child in sorted(category.children, key=lambda c: c.name)
        ]

    return data


@router.get("")
def list_categories(
    db: Session = Depends(get_db),
):
    top_level = db.scalars(
        select(Category)
        .where(Category.parent_id.is_(None))
        .order_by(Category.name)
    ).all()

    return [
        serialize_category(category, include_children=True)
        for category in top_level
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

    return serialize_category(category, include_children=True)


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

    if payload.parent_id is not None:
        parent = db.scalar(
            select(Category).where(Category.id == payload.parent_id)
        )

        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Parent category not found",
            )

    category = Category(
        name=payload.name,
        slug=slug,
        parent_id=payload.parent_id,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return serialize_category(category)


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

    if payload.parent_id is not None:
        if payload.parent_id == category_id:
            raise HTTPException(
                status_code=400,
                detail="A category cannot be its own parent",
            )

        parent = db.scalar(
            select(Category).where(Category.id == payload.parent_id)
        )

        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Parent category not found",
            )

        if parent.parent_id == category_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot set a child category as the parent",
            )

        category.parent_id = payload.parent_id

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

    return serialize_category(category)


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

    if category.children:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a category that has subcategories",
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

    subcategory_lists = db.scalars(
        select(LinkList).where(LinkList.subcategory_id == category_id)
    ).all()

    for link_list in subcategory_lists:
        link_list.subcategory_id = None

    db.execute(
        delete(UserExpertise).where(UserExpertise.category_id == category_id)
    )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted",
        "id": category_id,
        "moved_lists_to": fallback.id if fallback else None,
        "cleared_subcategory_lists": len(subcategory_lists),
    }
