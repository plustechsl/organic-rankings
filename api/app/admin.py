from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_admin, require_moderator
from app.models.link import Link
from app.models.link_report import LinkReport
from app.models.list import LinkList
from app.models.referral import Invitation
from app.models.user import User
from app.schemas.link import VERIFICATION_STATUSES


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


def serialize_invitation(invitation: Invitation) -> dict:
    return {
        "id": invitation.id,
        "inviter_id": invitation.inviter_id,
        "inviter_username": (
            invitation.inviter.username if invitation.inviter else None
        ),
        "invited_user_id": invitation.invited_user_id,
        "invited_username": (
            invitation.invited_user.username
            if invitation.invited_user
            else None
        ),
        "status": invitation.status,
        "points": invitation.points,
        "created_at": invitation.created_at,
        "reviewed_at": invitation.reviewed_at,
    }


@router.get("/test")
def admin_test(
    current_user: User = Depends(require_admin),
):
    return {
        "message": "Admin access granted",
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/users")
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.scalars(
        select(User).order_by(User.id)
    ).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.patch("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    allowed_roles = {
        "user",
        "contributor",
        "moderator",
        "admin",
    }

    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.id == current_user.id and role != "admin":
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin role",
        )

    user.role = role

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.patch("/lists/{list_id}/owner")
def change_list_owner(
    list_id: int,
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link_list = db.scalar(
        select(LinkList).where(LinkList.id == list_id)
    )

    if not link_list:
        raise HTTPException(
            status_code=404,
            detail="List not found",
        )

    new_owner = db.scalar(
        select(User).where(User.id == user_id)
    )

    if not new_owner or not new_owner.is_active:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    link_list.user_id = new_owner.id

    db.commit()
    db.refresh(link_list)

    return {
        "id": link_list.id,
        "user_id": link_list.user_id,
        "username": new_owner.username,
    }


@router.get("/invitations")
def list_invitations(
    status: str | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = (
        select(Invitation)
        .options(
            joinedload(Invitation.inviter),
            joinedload(Invitation.invited_user),
        )
        .order_by(Invitation.created_at.desc())
    )

    if status:
        query = query.where(Invitation.status == status)

    invitations = db.scalars(query).all()

    return [serialize_invitation(inv) for inv in invitations]


@router.post("/invitations/{invitation_id}/approve")
def approve_invitation(
    invitation_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    invitation = db.scalar(
        select(Invitation)
        .options(
            joinedload(Invitation.inviter),
            joinedload(Invitation.invited_user),
        )
        .where(Invitation.id == invitation_id)
    )

    if not invitation:
        raise HTTPException(
            status_code=404,
            detail="Invitation not found",
        )

    if invitation.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Invitation has already been reviewed",
        )

    invitation.status = "approved"
    invitation.reviewed_at = datetime.utcnow()
    invitation.reviewed_by_id = current_user.id

    db.commit()
    db.refresh(invitation)

    return serialize_invitation(invitation)


@router.post("/invitations/{invitation_id}/reject")
def reject_invitation(
    invitation_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    invitation = db.scalar(
        select(Invitation)
        .options(
            joinedload(Invitation.inviter),
            joinedload(Invitation.invited_user),
        )
        .where(Invitation.id == invitation_id)
    )

    if not invitation:
        raise HTTPException(
            status_code=404,
            detail="Invitation not found",
        )

    if invitation.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Invitation has already been reviewed",
        )

    invitation.status = "rejected"
    invitation.reviewed_at = datetime.utcnow()
    invitation.reviewed_by_id = current_user.id

    db.commit()
    db.refresh(invitation)

    return serialize_invitation(invitation)


@router.patch("/users/{user_id}/status")
def change_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin),
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

    if user.id == current_user.id and not is_active:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account",
        )

    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.get("/reports")
def list_reports(
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(
            Link.id,
            Link.title,
            Link.url,
            Link.verification_status,
            Link.verified_at,
            func.count(LinkReport.id).label("report_count"),
            func.max(LinkReport.created_at).label("last_reported_at"),
        )
        .join(LinkReport, LinkReport.link_id == Link.id)
        .group_by(Link.id)
        .order_by(
            func.count(LinkReport.id).desc(),
            func.max(LinkReport.created_at).desc(),
        )
    ).all()

    if not rows:
        return []

    reports = db.scalars(
        select(LinkReport).where(
            LinkReport.link_id.in_([row.id for row in rows])
        )
    ).all()

    usernames = {
        user.id: user.username
        for user in db.scalars(
            select(User).where(
                User.id.in_([report.user_id for report in reports])
            )
        ).all()
    }

    by_link: dict[int, list[dict]] = {}

    for report in reports:
        by_link.setdefault(report.link_id, []).append(
            {
                "id": report.id,
                "user_id": report.user_id,
                "username": usernames.get(report.user_id),
                "reason": report.reason,
                "created_at": report.created_at,
            }
        )

    return [
        {
            "link_id": row.id,
            "title": row.title,
            "url": row.url,
            "report_count": row.report_count,
            "last_reported_at": row.last_reported_at,
            "verification_status": row.verification_status,
            "verified_at": row.verified_at,
            "reports": by_link.get(row.id, []),
        }
        for row in rows
    ]


@router.post("/reports/{link_id}/resolve")
def resolve_reports(
    link_id: int,
    verdict: str,
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
):
    if verdict not in (*VERIFICATION_STATUSES, "none"):
        raise HTTPException(
            status_code=400,
            detail="Invalid verdict",
        )

    link = db.scalar(
        select(Link).where(Link.id == link_id)
    )

    if not link:
        raise HTTPException(
            status_code=404,
            detail="Link not found",
        )

    link.verification_status = None if verdict == "none" else verdict
    link.verified_by_id = None if verdict == "none" else current_user.id
    link.verified_at = None if verdict == "none" else datetime.utcnow()

    db.commit()
    db.refresh(link)

    return {
        "link_id": link.id,
        "verification_status": link.verification_status,
        "verified_at": link.verified_at,
        "verified_by": current_user.username if link.verification_status else None,
    }
