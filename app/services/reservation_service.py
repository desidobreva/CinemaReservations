from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.reservation import Reservation, ReservationTicket, ReservationStatus
from app.models.cinema import Screening
from app.models.user import User
from app.schemas.reservation import ReservationCreateIn


def create_reservation(db: Session, user: User, data: ReservationCreateIn) -> Reservation:
    screening = db.get(Screening, data.screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    # валидираме граници на седалките спрямо залата
    hall = screening.hall
    for s in data.seats:
        if s.seat_row > hall.rows or s.seat_col > hall.cols:
            raise HTTPException(status_code=400, detail="Seat out of hall bounds")

    reservation = Reservation(
        user_id=user.id,
        screening_id=screening.id,
        status=ReservationStatus.PENDING,
        notes=data.notes,
    )
    db.add(reservation)
    db.flush()  # да вземем reservation.id преди tickets

    for s in data.seats:
        db.add(
            ReservationTicket(
                reservation_id=reservation.id,
                screening_id=screening.id,
                seat_row=s.seat_row,
                seat_col=s.seat_col,
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # UniqueConstraint -> някой вече е резервирал това място
        raise HTTPException(status_code=409, detail="One or more seats already booked") from exc

    db.refresh(reservation)
    return reservation
