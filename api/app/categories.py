from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.category import Category
from app.models.list import LinkList
from app.models.user import User
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

    referencing_list = db.scalar(
        select(LinkList).where(
            (LinkList.category_id == category_id)
            | (LinkList.subcategory_id == category_id)
        )
    )

    if referencing_list:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a category that is used by existing lists",
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted",
        "id": category_id,
    }
