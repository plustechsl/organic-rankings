from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.link import Link
from app.models.link_tag import LinkTag
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import LinkTagsAttach
from app.utils import slugify


router = APIRouter(
    tags=["Tags"],
)

MAX_TAGS_PER_LINK = 10
TAG_SIMILARITY_THRESHOLD = 0.85


def serialize_tag(tag: Tag) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "slug": tag.slug,
        "created_at": tag.created_at,
    }


def _find_similar_tag(name: str, db: Session, slug: str) -> Tag | None:
    candidates = db.scalars(select(Tag)).all()
    target = name.replace("-", " ")
    target_slug = slug.replace("-", " ")

    for candidate in candidates:
        if candidate.slug == slug:
            continue

        candidate_name = candidate.name.replace("-", " ")
        ratio = SequenceMatcher(None, target, candidate_name).ratio()
        if ratio >= TAG_SIMILARITY_THRESHOLD:
            return candidate

        ratio_slug = SequenceMatcher(None, target_slug, candidate.slug.replace("-", " ")).ratio()
        if ratio_slug >= TAG_SIMILARITY_THRESHOLD:
            return candidate

    return None


def get_or_create_tag(name: str, db: Session) -> Tag:
    slug = slugify(name)

    if not slug:
        raise HTTPException(
            status_code=400,
            detail=f"Could not generate a valid slug from tag '{name}'",
        )

    tag = db.scalar(select(Tag).where(Tag.slug == slug))

    if tag:
        return tag

    similar = _find_similar_tag(name, db, slug)
    if similar:
        raise HTTPException(
            status_code=400,
            detail=f"Tag '{name}' is too similar to existing tag '{similar.name}'. Use '{similar.name}' instead.",
        )

    tag = Tag(name=name.strip().lower().replace(" ", "-"), slug=slug)
    db.add(tag)
    db.flush()

    return tag


def can_manage_link(link: Link, current_user: User) -> bool:
    is_link_owner = link.user_id == current_user.id
    is_privileged = current_user.role in {"admin", "moderator"}
    return is_link_owner or is_privileged


@router.get("/tags")
def list_tags(
    db: Session = Depends(get_db),
):
    tags = db.scalars(
        select(Tag).order_by(Tag.name)
    ).all()

    return [serialize_tag(tag) for tag in tags]


@router.get("/tags/{tag_id}")
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
):
    tag = db.scalar(
        select(Tag).where(Tag.id == tag_id)
    )

    if not tag:
        raise HTTPException(
            status_code=404,
            detail="Tag not found",
        )

    return serialize_tag(tag)


@router.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tag = db.scalar(
        select(Tag).where(Tag.id == tag_id)
    )

    if not tag:
        raise HTTPException(
            status_code=404,
            detail="Tag not found",
        )

    db.delete(tag)
    db.commit()

    return {
        "message": "Tag deleted",
        "id": tag_id,
    }


@router.get("/links/{link_id}/tags")
def list_link_tags(
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

    tags = sorted(
        (relation.tag for relation in link.tag_relations),
        key=lambda tag: tag.name,
    )

    return [serialize_tag(tag) for tag in tags]


@router.post("/links/{link_id}/tags", status_code=201)
def attach_tags_to_link(
    link_id: int,
    payload: LinkTagsAttach,
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
            detail="You do not have permission to modify tags on this link",
        )

    existing_tag_ids = {
        relation.tag_id for relation in link.tag_relations
    }

    new_tag_ids_seen = set()
    new_tags = []

    for name in payload.tags:
        tag = get_or_create_tag(name, db)

        if tag.id in existing_tag_ids or tag.id in new_tag_ids_seen:
            continue

        new_tag_ids_seen.add(tag.id)
        new_tags.append(tag)

    total_after = len(existing_tag_ids) + len(new_tags)

    if total_after > MAX_TAGS_PER_LINK:
        raise HTTPException(
            status_code=400,
            detail=(
                f"A link can have at most {MAX_TAGS_PER_LINK} tags "
                f"(currently {len(existing_tag_ids)}, "
                f"trying to add {len(new_tags)} more)"
            ),
        )

    for tag in new_tags:
        db.add(LinkTag(link_id=link.id, tag_id=tag.id))

    db.commit()
    db.refresh(link)

    tags = sorted(
        (relation.tag for relation in link.tag_relations),
        key=lambda tag: tag.name,
    )

    return [serialize_tag(tag) for tag in tags]


@router.delete("/links/{link_id}/tags/{tag_id}")
def detach_tag_from_link(
    link_id: int,
    tag_id: int,
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
            detail="You do not have permission to modify tags on this link",
        )

    relation = db.scalar(
        select(LinkTag).where(
            LinkTag.link_id == link_id,
            LinkTag.tag_id == tag_id,
        )
    )

    if not relation:
        raise HTTPException(
            status_code=404,
            detail="Tag is not attached to this link",
        )

    db.delete(relation)
    db.commit()
    db.refresh(link)

    return {
        "message": "Tag removed from link",
        "link_id": link_id,
        "tag_id": tag_id,
    }
