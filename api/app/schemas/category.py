from pydantic import BaseModel, field_validator


class CategoryCreate(BaseModel):
    name: str
    slug: str | None = None
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name cannot be empty")
        return value.strip()


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    parent_id: int | None = None
