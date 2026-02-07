from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class MovieCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: str = "General"


class MovieOut(BaseModel):
    id: int
    title: str
    description: str
    category: str


class HallCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rows: int = Field(ge=1, le=100)
    cols: int = Field(ge=1, le=100)


class HallOut(BaseModel):
    id: int
    name: str
    rows: int
    cols: int


class ScreeningCreateIn(BaseModel):
    movie_id: int
    hall_id: int
    starts_at: datetime


class ScreeningOut(BaseModel):
    id: int
    movie_id: int
    hall_id: int
    starts_at: datetime
    provider_id: int

class MovieUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None


class HallUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    rows: Optional[int] = Field(default=None, ge=1, le=100)
    cols: Optional[int] = Field(default=None, ge=1, le=100)


class ScreeningUpdateIn(BaseModel):
    movie_id: Optional[int] = None
    hall_id: Optional[int] = None
    starts_at: Optional[datetime] = None