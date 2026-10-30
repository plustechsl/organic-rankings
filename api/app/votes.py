from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.link import Link
from app.models.list import LinkList
from app.models.user import User
from app.models.user_expertise import UserExpertise
from app.models.vote import Vote
from app.net import get_client_ip
from app.ratelimit import limit_vote
from app.utils import hash_ip


router = APIRouter(
    tags=["Votes"],
)

REGISTERED_POINTS = 1
EXPERTISE_MATCH_POINTS = 3


@router.post("/links/{link_id}/vote", status_code=201)
def vote_link(
    link_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit_vote(request, current_user.id)

    link = db.scalar(
        select(Link).where(Link.id == link_id)
    )

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found",
        )

    link_list = db.scalar(
        select(LinkList).where(LinkList.id == link.list_id)
    )

    ip = get_client_ip(request)
    ip_hash = hash_ip(ip)

    existing = db.scalar(
        select(Vote).where(
            Vote.link_id == link_id,
            Vote.user_id == current_user.id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You have already voted for this link",
        )

    points = REGISTERED_POINTS

    expertise_category_ids = {
        e.category_id
        for e in db.scalars(
            select(UserExpertise).where(
                UserExpertise.user_id == current_user.id
            )
        ).all()
    }

    if link_list and link_list.category_id in expertise_category_ids:
        points = EXPERTISE_MATCH_POINTS

    vote = Vote(
        link_id=link_id,
        user_id=current_user.id,
        ip_hash=ip_hash,
        points=points,
    )

    db.add(vote)

    link.points += points

    db.commit()
    db.refresh(link)

    return {
        "link_id": link.id,
        "points_awarded": points,
        "link_total_points": link.points,
    }


@router.delete("/links/{link_id}/vote")
def remove_vote(
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

    vote = db.scalar(
        select(Vote).where(
            Vote.link_id == link_id,
            Vote.user_id == current_user.id,
        )
    )

    if not vote:
        raise HTTPException(
            status_code=404,
            detail="You have not voted for this link",
        )

    link.points -= vote.points

    db.delete(vote)
    db.commit()
    db.refresh(link)

    return {
        "link_id": link.id,
        "link_total_points": link.points,
    }


@router.get("/me/votes")
def list_my_votes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    votes = db.scalars(
        select(Vote).where(Vote.user_id == current_user.id)
    ).all()

    return [
        {
            "link_id": v.link_id,
            "points": v.points,
        }
        for v in votes
    ]
