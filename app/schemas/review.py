from pydantic import BaseModel, Field


class ReviewCreateIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class ReviewOut(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: int
    comment: str
