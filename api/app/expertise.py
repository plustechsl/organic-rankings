from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category import Category
from app.models.user import User
from app.models.user_expertise import UserExpertise
from app.schemas.expertise import ExpertiseAdd


router = APIRouter(
    prefix="/me/expertise",
    tags=["User Expertise"],
)

MAX_EXPERTISES = 3


def serialize_expertise(expertise: UserExpertise) -> dict:
    return {
        "category_id": expertise.category_id,
        "category_name": expertise.category.name,
        "category_slug": expertise.category.slug,
        "created_at": expertise.created_at,
    }


@router.get("")
def list_my_expertise(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expertises = db.scalars(
        select(UserExpertise)
        .where(UserExpertise.user_id == current_user.id)
        .order_by(UserExpertise.created_at)
    ).all()

    return [serialize_expertise(e) for e in expertises]


@router.post("", status_code=201)
def add_my_expertise(
    payload: ExpertiseAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = db.scalar(
        select(Category).where(Category.id == payload.category_id)
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    existing = db.scalar(
        select(UserExpertise).where(
            UserExpertise.user_id == current_user.id,
            UserExpertise.category_id == payload.category_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This category is already one of your expertises",
        )

    current_count = db.scalar(
        select(UserExpertise).where(
            UserExpertise.user_id == current_user.id,
        )
    )

    count = len(
        db.scalars(
            select(UserExpertise).where(
                UserExpertise.user_id == current_user.id,
            )
        ).all()
    )

    if count >= MAX_EXPERTISES:
        raise HTTPException(
            status_code=400,
            detail=f"You can have at most {MAX_EXPERTISES} expertises",
        )

    expertise = UserExpertise(
        user_id=current_user.id,
        category_id=payload.category_id,
    )

    db.add(expertise)
    db.commit()
    db.refresh(expertise)

    return serialize_expertise(expertise)


@router.delete("/{category_id}")
def remove_my_expertise(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expertise = db.scalar(
        select(UserExpertise).where(
            UserExpertise.user_id == current_user.id,
            UserExpertise.category_id == category_id,
        )
    )

    if not expertise:
        raise HTTPException(
            status_code=404,
            detail="This category is not one of your expertises",
        )

    db.delete(expertise)
    db.commit()

    return {
        "message": "Expertise removed",
        "category_id": category_id,
    }
