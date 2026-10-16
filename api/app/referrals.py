import secrets

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.config import REFERRAL_POINTS
from app.database import get_db
from app.dependencies import get_current_user
from app.models.referral import Invitation, ReferralCode
from app.models.user import User


router = APIRouter(
    prefix="/me/referrals",
    tags=["Referrals"],
)


def get_or_create_referral_code(user_id: int, db: Session) -> ReferralCode:
    referral_code = db.scalar(
        select(ReferralCode).where(ReferralCode.user_id == user_id)
    )

    if referral_code:
        return referral_code

    while True:
        code = secrets.token_urlsafe(6)

        existing = db.scalar(
            select(ReferralCode).where(ReferralCode.code == code)
        )

        if not existing:
            break

    referral_code = ReferralCode(
        user_id=user_id,
        code=code,
    )

    db.add(referral_code)
    db.commit()
    db.refresh(referral_code)

    return referral_code


def get_referral_points(user_id: int, db: Session) -> int:
    points = db.scalar(
        select(func.coalesce(func.sum(Invitation.points), 0)).where(
            Invitation.inviter_id == user_id,
            Invitation.status == "approved",
        )
    )

    return int(points or 0)


def serialize_invitation(invitation: Invitation) -> dict:
    return {
        "id": invitation.id,
        "user_id": invitation.invited_user_id,
        "username": (
            invitation.invited_user.username
            if invitation.invited_user
            else None
        ),
        "status": invitation.status,
        "points": invitation.points,
        "created_at": invitation.created_at,
        "reviewed_at": invitation.reviewed_at,
    }


@router.get("")
def get_my_referrals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral_code = get_or_create_referral_code(current_user.id, db)

    invitations = db.scalars(
        select(Invitation)
        .options(joinedload(Invitation.invited_user))
        .where(Invitation.inviter_id == current_user.id)
        .order_by(Invitation.created_at.desc())
    ).all()

    return {
        "code": referral_code.code,
        "points": get_referral_points(current_user.id, db),
        "points_per_invite": REFERRAL_POINTS,
        "invited": [serialize_invitation(inv) for inv in invitations],
    }
