from pydantic import BaseModel


class ExpertiseAdd(BaseModel):
    category_id: int
