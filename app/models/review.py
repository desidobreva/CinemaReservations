from sqlalchemy import ForeignKey, Integer, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)

    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(2000), default="")

    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="chk_rating_1_5"),)
