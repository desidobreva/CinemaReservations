from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Movie(Base):
    __tablename__ = "movies"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(String(2000), default="")
    category: Mapped[str] = mapped_column(String(100), default="General")


class Hall(Base):
    __tablename__ = "halls"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    rows: Mapped[int] = mapped_column(Integer)
    cols: Mapped[int] = mapped_column(Integer)


class Screening(Base):
    __tablename__ = "screenings"
    id: Mapped[int] = mapped_column(primary_key=True)

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"))
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id"))

    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    movie = relationship("Movie")
    hall = relationship("Hall")
