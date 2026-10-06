from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.user_reputation import UserReputation


router = APIRouter(
    tags=["Reputation"],
)


@router.get("/users/{user_id}/reputation")
def get_user_reputation(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    count = db.scalar(
        select(func.count())
        .select_from(UserReputation)
        .where(UserReputation.to_user_id == user_id)
    )

    return {
        "user_id": user_id,
        "username": user.username,
        "reputation": count or 0,
    }


@router.post("/users/{user_id}/reputation", status_code=201)
def give_reputation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot give reputation to yourself",
        )

    target_user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    existing = db.scalar(
        select(UserReputation).where(
            UserReputation.from_user_id == current_user.id,
            UserReputation.to_user_id == user_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You have already given reputation to this user",
        )

    reputation = UserReputation(
        from_user_id=current_user.id,
        to_user_id=user_id,
    )

    db.add(reputation)
    db.commit()

    count = db.scalar(
        select(func.count())
        .select_from(UserReputation)
        .where(UserReputation.to_user_id == user_id)
    )

    return {
        "user_id": user_id,
        "username": target_user.username,
        "reputation": count or 0,
    }
