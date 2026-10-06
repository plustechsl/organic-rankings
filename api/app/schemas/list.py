from pydantic import BaseModel, field_validator


class ListCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str | None = None
    image_url: str | None = None
    category_id: int
    subcategory_id: int | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()


class ListUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    image_url: str | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
