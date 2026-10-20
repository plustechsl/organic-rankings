import re

from ddgs import DDGS
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.category import Category
from app.models.link import Link
from app.models.link_tag import LinkTag
from app.models.list import LinkList
from app.models.tag import Tag
from app.models.user import User
from app.utils import slugify


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


class SeedListRequest(BaseModel):
    topic: str
    category_name: str | None = None
    max_results: int = 8

    @field_validator("topic")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be empty")
        return value.strip()

    @field_validator("max_results")
    @classmethod
    def valid_range(cls, value: int) -> int:
        if value < 1 or value > 20:
            raise ValueError("max_results must be between 1 and 20")
        return value


STOPWORDS = {"de", "la", "el", "los", "las", "en", "con", "para", "y", "a"}


def derive_tags_from_topic(topic: str) -> list[str]:
    words = re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9]+", topic.lower())
    tags = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return tags[:5]


def build_list_description(results: list[dict], max_length: int = 280) -> str | None:
    sentences = []
    for r in results:
        description = r.get("description")
        if not description:
            continue
        first_sentence = re.split(r"(?<=[.!?])\s", description)[0].strip()
        if len(first_sentence) > 15:
            sentences.append(first_sentence)

    if not sentences:
        return None

    summary = ""
    for s in sentences:
        candidate = (summary + " " + s).strip() if summary else s
        if len(candidate) > max_length:
            break
        summary = candidate

    return summary or sentences[0][:max_length]


def search_topic(topic: str, max_results: int) -> list[dict]:
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(topic, max_results=max_results):
            title = (r.get("title") or "").strip()
            url = (r.get("href") or "").strip()
            body = (r.get("body") or "").strip()

            if not title or not url:
                continue

            results.append({
                "title": title[:200],
                "url": url[:1000],
                "description": body[:500] if body else None,
            })

    return results


def find_or_create_category(db: Session, category_name: str) -> Category:
    existing = db.scalar(
        select(Category).where(Category.name.ilike(category_name))
    )

    if existing:
        return existing

    slug = slugify(category_name)

    if not slug:
        raise HTTPException(
            status_code=400,
            detail="Could not generate a valid slug from category name",
        )

    slug_taken = db.scalar(select(Category).where(Category.slug == slug))
    if slug_taken:
        return slug_taken

    category = Category(name=category_name, slug=slug)
    db.add(category)
    db.flush()

    return category


def get_varios_category(db: Session) -> Category:
    bucket = db.scalar(
        select(Category).where(
            or_(
                Category.name.ilike("Varios"),
                Category.name.ilike("Cat varios"),
            )
        )
    )

    if bucket:
        return bucket

    return find_or_create_category(db, "Varios")


def resolve_category(db: Session, category_name: str) -> Category:
    existing = db.scalar(
        select(Category).where(Category.name.ilike(category_name))
    )

    if existing:
        return existing

    return get_varios_category(db)


def word_root(word: str) -> str:
    return word[:5]


def guess_category(db: Session, topic: str) -> Category:
    topic_words = set(re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]+", topic.lower()))
    topic_words = {w for w in topic_words if w not in STOPWORDS and len(w) > 2}
    topic_roots = {word_root(w) for w in topic_words}

    all_categories = db.scalars(select(Category)).all()

    best_match = None
    best_score = 0

    for cat in all_categories:
        cat_words = set(re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]+", cat.name.lower()))
        cat_roots = {word_root(w) for w in cat_words}
        score = len(topic_roots & cat_roots)
        if score > best_score:
            best_score = score
            best_match = cat

    if best_match:
        return best_match

    return get_varios_category(db)


def get_or_create_tag(db: Session, name: str) -> Tag | None:
    slug = slugify(name)

    if not slug:
        return None

    tag = db.scalar(select(Tag).where(Tag.slug == slug))
    if tag:
        return tag

    tag = Tag(name=name, slug=slug)
    db.add(tag)
    db.flush()

    return tag


@router.post("/seed-list")
def seed_list(
    payload: SeedListRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    results = search_topic(payload.topic, payload.max_results)

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron resultados para ese tema",
        )

    if payload.category_name:
        category = resolve_category(db, payload.category_name)
    else:
        category = guess_category(db, payload.topic)

    slug = slugify(payload.topic)
    if not slug:
        raise HTTPException(
            status_code=400,
            detail="Could not generate a valid slug from topic",
        )

    existing_list = db.scalar(select(LinkList).where(LinkList.slug == slug))
    if existing_list:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una lista con ese tema (slug duplicado)",
        )

    description = build_list_description(results)

    new_list = LinkList(
        user_id=current_user.id,
        category_id=category.id,
        title=payload.topic,
        slug=slug,
        description=description,
    )

    db.add(new_list)
    db.flush()

    tag_names = derive_tags_from_topic(payload.topic)
    tags = [t for t in (get_or_create_tag(db, name) for name in tag_names) if t]

    created_links = []

    for r in results:
        link = Link(
            list_id=new_list.id,
            user_id=current_user.id,
            title=r["title"],
            url=r["url"],
            description=r["description"],
        )
        db.add(link)
        db.flush()

        for tag in tags:
            db.add(LinkTag(link_id=link.id, tag_id=tag.id))

        created_links.append(link)

    db.commit()
    db.refresh(new_list)

    return {
        "id": new_list.id,
        "title": new_list.title,
        "slug": new_list.slug,
        "description": new_list.description,
        "category": category.name,
        "links_created": len(created_links),
        "tags": [t.name for t in tags],
    }
