from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.lists import serialize_list
from app.models.link import Link
from app.models.list import LinkList
from app.models.user import User


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def get_user_aura(user_id: int, db: Session) -> int:
    aura = db.scalar(
        select(func.coalesce(func.sum(Link.points), 0))
        .join(LinkList, Link.list_id == LinkList.id)
        .where(LinkList.user_id == user_id)
    )

    return int(aura or 0)


@router.get("")
def list_users(
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(
            User,
            func.coalesce(func.sum(Link.points), 0).label("aura"),
        )
        .outerjoin(LinkList, LinkList.user_id == User.id)
        .outerjoin(Link, Link.list_id == LinkList.id)
        .where(User.is_active.is_(True))
        .group_by(User.id)
        .order_by(
            func.coalesce(func.sum(Link.points), 0).desc(),
            User.username,
        )
    ).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at,
            "aura": int(aura or 0),
        }
        for user, aura in rows
    ]


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    lists = db.scalars(
        select(LinkList)
        .options(joinedload(LinkList.user), selectinload(LinkList.links))
        .where(LinkList.user_id == user_id)
    ).all()

    lists = sorted(
        lists,
        key=lambda link_list: (
            sum(link.points for link in link_list.links),
            link_list.created_at,
        ),
        reverse=True,
    )

    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
        "aura": get_user_aura(user_id, db),
        "lists": [serialize_list(link_list) for link_list in lists],
    }
