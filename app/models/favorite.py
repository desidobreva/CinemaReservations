from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FavoriteMovie(Base):
    __tablename__ = "favorite_movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)

    __table_args__ = (UniqueConstraint("user_id", "movie_id", name="uq_user_movie_fav"),)
