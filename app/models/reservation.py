"""Reservation and ReservationTicket ORM models.

Defines database schema for cinema seat reservations and individual
ticket records.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, DateTime, Enum, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReservationStatus(str, enum.Enum):
    PENDING = "PENDING"     
    CONFIRMED = "CONFIRMED" 
    CANCELED = "CANCELED"    
    COMPLETED = "COMPLETED" 


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus), default=ReservationStatus.PENDING)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)   
    screening_id: Mapped[int] = mapped_column(ForeignKey("screenings.id"), index=True)

    notes: Mapped[str] = mapped_column(String(1000), default="")

    user = relationship("User")
    screening = relationship("Screening")
    tickets = relationship(
    "ReservationTicket",
    cascade="all, delete-orphan",
    back_populates="reservation",
    )


class ReservationTicket(Base):
    __tablename__ = "reservation_tickets"
    reservation = relationship("Reservation", back_populates="tickets")

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), index=True)
    screening_id: Mapped[int] = mapped_column(ForeignKey("screenings.id"), index=True)

    seat_row: Mapped[int] = mapped_column(Integer)
    seat_col: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("screening_id", "seat_row", "seat_col", name="uq_screening_seat"),
    )