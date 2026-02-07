from pydantic import BaseModel


class FavoriteOut(BaseModel):
    id: int
    user_id: int
    movie_id: int
