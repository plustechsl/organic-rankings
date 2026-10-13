from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category import Category
from app.models.list import LinkList
from app.models.user import User
from app.schemas.list import ListCreate, ListUpdate
from app.utils import slugify


router = APIRouter(
    prefix="/lists",
    tags=["Lists"],
)


def serialize_list(link_list: LinkList) -> dict:
    return {
        "id": link_list.id,
        "user_id": link_list.user_id,
        "username": link_list.user.username if link_list.user else None,
        "title": link_list.title,
        "slug": link_list.slug,
        "description": link_list.description,
        "image_url": link_list.image_url,
        "points": link_list.points,
        "category_id": link_list.category_id,
        "subcategory_id": link_list.subcategory_id,
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


def validate_category_and_subcategory(
    category_id: int,
    subcategory_id: int | None,
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

    if subcategory_id is not None:
        subcategory = db.scalar(
            select(Category).where(Category.id == subcategory_id)
        )

        if not subcategory:
            raise HTTPException(
                status_code=404,
                detail="Subcategory not found",
            )

        if subcategory.parent_id != category_id:
            raise HTTPException(
                status_code=400,
                detail="Subcategory must be a child of the selected category",
            )


@router.get("")
def list_lists(
    db: Session = Depends(get_db),
):
    lists = db.scalars(
        select(LinkList)
        .options(joinedload(LinkList.user))
        .order_by(LinkList.created_at.desc())
    ).all()

    return [serialize_list(link_list) for link_list in lists]


@router.get("/{list_id}")
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
):
    link_list = db.scalar(
        select(LinkList)
        .options(joinedload(LinkList.user))
        .where(LinkList.id == list_id)
    )

    if not link_list:
        raise HTTPException(
            status_code=404,
            detail="List not found",
        )

    return serialize_list(link_list)


@router.post("", status_code=201)
def create_list(
    payload: ListCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_category_and_subcategory(
        payload.category_id,
        payload.subcategory_id,
        db,
    )

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
        subcategory_id=payload.subcategory_id,
        title=payload.title,
        slug=slug,
        description=payload.description,
        image_url=payload.image_url,
    )

    db.add(link_list)
    db.commit()
    db.refresh(link_list)

    return serialize_list(link_list)


@router.patch("/{list_id}")
def update_list(
    list_id: int,
    payload: ListUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link_list = get_owned_list_or_403(list_id, current_user, db)

    new_category_id = (
        payload.category_id
        if payload.category_id is not None
        else link_list.category_id
    )

    new_subcategory_id = (
        payload.subcategory_id
        if payload.subcategory_id is not None
        else link_list.subcategory_id
    )

    if payload.category_id is not None or payload.subcategory_id is not None:
        validate_category_and_subcategory(
            new_category_id,
            new_subcategory_id,
            db,
        )

    link_list.category_id = new_category_id
    link_list.subcategory_id = new_subcategory_id

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

    db.delete(link_list)
    db.commit()

    return {
        "message": "List deleted",
        "id": list_id,
    }
