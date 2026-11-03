import re
from typing import Literal

from pydantic import BaseModel, field_validator

Sensitivity = Literal["none", "adult", "violence"]

MAX_TAGS = 10


def clean_tag_list(value: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for tag in value:
        if not isinstance(tag, str):
            continue

        name = re.sub(r"\s+", " ", tag.strip()).lower()

        if not name:
            continue
        if len(name) < 2:
            raise ValueError("Tag must be at least 2 characters")
        if len(name) > 32:
            raise ValueError("Tag must be at most 32 characters")
        if not re.fullmatch(r"[^\W_]+(?:[ -][^\W_]+)*", name):
            raise ValueError(
                f"Invalid tag: '{tag}'. Use only letters, numbers, spaces or hyphens"
            )

        name = name.replace(" ", "-")

        if name in seen:
            continue

        seen.add(name)
        cleaned.append(name)

    if len(cleaned) > MAX_TAGS:
        raise ValueError(f"A link can have at most {MAX_TAGS} tags")

    return cleaned


class LinkCreate(BaseModel):
    list_id: int
    title: str
    url: str
    description: str | None = None
    image_url: str | None = None
    sensitivity: Sensitivity = "none"
    tags: list[str] = []

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()

    @field_validator("url")
    @classmethod
    def url_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("URL cannot be empty")
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return value

    @field_validator("tags")
    @classmethod
    def tags_valid(cls, value: list[str]) -> list[str]:
        return clean_tag_list(value)


class LinkPreviewRequest(BaseModel):
    list_id: int
    url: str

    @field_validator("url")
    @classmethod
    def url_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("URL cannot be empty")
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


class LinkUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    description: str | None = None
    image_url: str | None = None
    sensitivity: Sensitivity | None = None