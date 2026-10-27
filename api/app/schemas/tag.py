import re

from pydantic import BaseModel, field_validator


class LinkTagsAttach(BaseModel):
    tags: list[str]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for t in value:
            if not isinstance(t, str):
                continue
            if not t.strip():
                continue

            name = re.sub(r"\s+", " ", t.strip()).lower()

            if len(name) < 2:
                raise ValueError("Tag must be at least 2 characters")
            if len(name) > 32:
                raise ValueError("Tag must be at most 32 characters")

            if not re.fullmatch(r"[a-z0-9]+(?:[ -][a-z0-9]+)*", name):
                raise ValueError(
                    f"Invalid tag: '{t}'. Use only letters, numbers, spaces or hyphens"
                )

            name = name.replace(" ", "-")

            if name in seen:
                continue
            seen.add(name)
            cleaned.append(name)

        if not cleaned:
            raise ValueError("At least one valid tag is required")
        return cleaned
