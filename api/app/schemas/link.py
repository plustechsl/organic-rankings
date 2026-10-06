from pydantic import BaseModel, field_validator


class LinkCreate(BaseModel):
    list_id: int
    title: str
    url: str
    description: str | None = None
    image_url: str | None = None

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


class LinkUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    description: str | None = None
    image_url: str | None = None
