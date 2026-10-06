from pydantic import BaseModel, field_validator


class LinkTagsAttach(BaseModel):
    tags: list[str]

    @field_validator("tags")
    @classmethod
    def tags_not_empty(cls, value: list[str]) -> list[str]:
        cleaned = [t.strip() for t in value if t.strip()]
        if not cleaned:
            raise ValueError("At least one tag is required")
        return cleaned
