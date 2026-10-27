from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.ratelimit import limit_creation
from app.models.link import Link
from app.models.list import LinkList
from app.models.user import User
from app.schemas.link import LinkCreate, LinkUpdate
from datetime import datetime, timedelta

from app.ai_detect import analyze_text
from app.page_fetch import fetch_page_text


router = APIRouter(
    prefix="/links",
    tags=["Links"],
)


def serialize_link(link: Link) -> dict:
    return {
        "id": link.id,
        "list_id": link.list_id,
        "user_id": link.user_id,
        "title": link.title,
        "url": link.url,
        "description": link.description,
        "image_url": link.image_url,
        "points": link.points,
        "created_at": link.created_at,
        "updated_at": link.updated_at,
        "ai_score": link.ai_score,
        "ai_checked_at": link.ai_checked_at,
    }


def can_manage_link(link: Link, current_user: User) -> bool:
    is_link_owner = link.user_id == current_user.id
    is_privileged = current_user.role in {"admin", "moderator"}
    return is_link_owner or is_privileged


def can_add_to_list(link_list: LinkList, current_user: User) -> bool:
    is_list_owner = link_list.user_id == current_user.id
    is_privileged = current_user.role in {"admin", "moderator"}
    return is_list_owner or is_privileged


@router.get("")
def list_links(
    list_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Link).order_by(Link.points.desc(), Link.created_at.desc())

    if list_id is not None:
        query = query.where(Link.list_id == list_id)

    links = db.scalars(query).all()

    return [serialize_link(link) for link in links]


@router.get("/{link_id}")
def get_link(
    link_id: int,
    db: Session = Depends(get_db),
):
    link = db.scalar(
        select(Link).where(Link.id == link_id)
    )

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found",
        )

    return serialize_link(link)


@router.post("", status_code=201)
def create_link(
    payload: LinkCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit_creation(request, current_user.id)

    link_list = db.scalar(
        select(LinkList).where(LinkList.id == payload.list_id)
    )

    if not link_list:
        raise HTTPException(
            status_code=404,
            detail="List not found",
        )

    if not can_add_to_list(link_list, current_user):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to add links to this list",
        )

    link = Link(
        list_id=payload.list_id,
        user_id=current_user.id,
        title=payload.title,
        url=payload.url,
        description=payload.description,
        image_url=payload.image_url,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return serialize_link(link)


@router.patch("/{link_id}")
def update_link(
    link_id: int,
    payload: LinkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
        if payload.url is not None:
            if payload.url != link.url:
                link.ai_score = None
                link.ai_checked_at = None
            link.url = payload.url
):
    link = db.scalar(
        select(Link).where(Link.id == link_id)
    )

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found",
        )

    if not can_manage_link(link, current_user):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to modify this link",
        )

    if payload.title is not None:
        link.title = payload.title

    if payload.url is not None:
        link.url = payload.url

    if payload.description is not None:
        link.description = payload.description

    if payload.image_url is not None:
        link.image_url = payload.image_url

    db.commit()
    db.refresh(link)

    return serialize_link(link)


@router.delete("/{link_id}")
def delete_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.scalar(
        select(Link).where(Link.id == link_id)
    )

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found",
        )

    if not can_manage_link(link, current_user):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this link",
        )

    db.delete(link)
    db.commit()

    return {
        "message": "Link deleted",
        "id": link_id,
    }
    AI_CHECK_TTL = timedelta(days=1)


    @router.post("/{link_id}/ai-check")
    def ai_check_link(
        link_id: int,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        limit_creation(request, current_user.id)

        link = db.scalar(select(Link).where(Link.id == link_id))

        if not link:
            raise HTTPException(status_code=404, detail="Link not found")

        if link.ai_checked_at and datetime.utcnow() - link.ai_checked_at < AI_CHECK_TTL:
            return serialize_link(link)

        try:
            page_text = fetch_page_text(link.url)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        result = analyze_text(page_text)

        link.ai_score = result["score"] if result else None
        link.ai_checked_at = datetime.utcnow()

        db.commit()
        db.refresh(link)

        return serialize_link(link)
