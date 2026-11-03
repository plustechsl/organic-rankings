import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.link import Link
from app.models.link_request import LinkRequest
from app.models.link_tag import LinkTag
from app.models.list import LinkList
from app.models.user import User
from app.ratelimit import limit_creation
from app.schemas.link_request import LinkRequestCreate, LinkRequestReview
from app.tags import get_or_create_tag


router = APIRouter(
    prefix="/link-requests",
    tags=["Link requests"],
)


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []

    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return []

    if not isinstance(value, list):
        return []

    return [str(tag) for tag in value]


def serialize_request(link_request: LinkRequest) -> dict:
    return {
        "id": link_request.id,
        "list_id": link_request.list_id,
        "user_id": link_request.user_id,
        "username": (
            link_request.requester.username
            if link_request.requester
            else None
        ),
        "title": link_request.title,
        "url": link_request.url,
        "description": link_request.description,
        "tags": parse_tags(link_request.tags),
        "sensitivity": link_request.sensitivity,
        "status": link_request.status,
        "created_at": link_request.created_at,
        "reviewed_at": link_request.reviewed_at,
        "reviewed_by": link_request.reviewed_by,
        "reviewer_username": (
            link_request.reviewer.username
            if link_request.reviewer
            else None
        ),
    }


def get_list_or_404(list_id: int, db: Session) -> LinkList:
    link_list = db.scalar(
        select(LinkList).where(LinkList.id == list_id)
    )

    if not link_list:
        raise HTTPException(
            status_code=404,
            detail="List not found",
        )

    return link_list


def can_review(link_list: LinkList, current_user: User) -> bool:
    return (
        current_user.role == "admin"
        or link_list.user_id == current_user.id
    )


@router.post("", status_code=201)
def create_link_request(
    payload: LinkRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit_creation(request, current_user.id)

    link_list = get_list_or_404(payload.list_id, db)

    if can_review(link_list, current_user):
        raise HTTPException(
            status_code=400,
            detail=(
                "No necesitas aprobación para añadir enlaces "
                "a esta lista."
            ),
        )

    existing = db.scalar(
        select(LinkRequest).where(
            LinkRequest.list_id == payload.list_id,
            LinkRequest.user_id == current_user.id,
            LinkRequest.url == payload.url,
            LinkRequest.status == "pending",
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya tienes una solicitud pendiente para este enlace.",
        )

    link_request = LinkRequest(
        list_id=payload.list_id,
        user_id=current_user.id,
        title=payload.title,
        url=payload.url,
        description=payload.description,
        tags=json.dumps(payload.tags),
        sensitivity=payload.sensitivity,
    )

    db.add(link_request)
    db.commit()
    db.refresh(link_request)

    return serialize_request(link_request)


@router.get("/mine")
def list_my_requests(
    list_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(LinkRequest)
        .options(
            joinedload(LinkRequest.requester),
            joinedload(LinkRequest.reviewer),
        )
        .where(LinkRequest.user_id == current_user.id)
    )

    if list_id is not None:
        query = query.where(LinkRequest.list_id == list_id)

    requests = db.scalars(
        query.order_by(LinkRequest.created_at.desc())
    ).all()

    return [serialize_request(link_request) for link_request in requests]


@router.get("")
def list_link_requests(
    list_id: int,
    status: str = "pending",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link_list = get_list_or_404(list_id, db)

    if not can_review(link_list, current_user):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to review this list",
        )

    query = (
        select(LinkRequest)
        .options(
            joinedload(LinkRequest.requester),
            joinedload(LinkRequest.reviewer),
        )
        .where(LinkRequest.list_id == list_id)
    )

    if status != "all":
        query = query.where(LinkRequest.status == status)

    requests = db.scalars(
        query.order_by(LinkRequest.created_at.asc())
    ).all()

    return [serialize_request(link_request) for link_request in requests]


@router.patch("/{request_id}")
def review_link_request(
    request_id: int,
    payload: LinkRequestReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link_request = db.scalar(
        select(LinkRequest)
        .options(joinedload(LinkRequest.link_list))
        .where(LinkRequest.id == request_id)
    )

    if not link_request:
        raise HTTPException(
            status_code=404,
            detail="Link request not found",
        )

    if not can_review(link_request.link_list, current_user):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to review this request",
        )

    if link_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="This request has already been reviewed",
        )

    link_id = None

    if payload.action == "approve":
        link = Link(
            list_id=link_request.list_id,
            user_id=link_request.user_id,
            title=link_request.title,
            url=link_request.url,
            description=link_request.description,
            sensitivity=link_request.sensitivity,
        )

        db.add(link)
        db.flush()

        for name in parse_tags(link_request.tags):
            tag = get_or_create_tag(name, db)
            db.add(LinkTag(link_id=link.id, tag_id=tag.id))

        link_id = link.id

    link_request.status = (
        "approved" if payload.action == "approve" else "rejected"
    )
    link_request.reviewed_by = current_user.id
    link_request.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(link_request)

    result = serialize_request(link_request)
    result["link_id"] = link_id

    return result
