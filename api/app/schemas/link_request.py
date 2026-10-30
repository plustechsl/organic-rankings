from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.link import Sensitivity, clean_tag_list


class LinkRequestCreate(BaseModel):
    list_id: int
    title: str
    url: str
    description: str | None = None
    tags: list[str] = []
    sensitivity: Sensitivity = "none"

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


class LinkRequestReview(BaseModel):
    action: Literal["approve", "reject"]
