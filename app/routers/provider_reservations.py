from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.user import User, UserRole
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.reservation import ReservationOut, ReservationTicketOut

router = APIRouter(prefix="/provider/reservations", tags=["provider-reservations"])


@router.get("", response_model=list[ReservationOut])
def list_incoming_reservations(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> list[ReservationOut]:
    # за по-строго: provider вижда само прожекциите, които е създал (screening.provider_id == user.id)
    # за простота: provider/admin вижда всички
    rows = db.query(Reservation).order_by(Reservation.id.desc()).all()
    return [
        ReservationOut(
            id=r.id,
            status=r.status,
            screening_id=r.screening_id,
            user_id=r.user_id,
            created_at=r.created_at,
            notes=r.notes,
            tickets=[ReservationTicketOut(seat_row=t.seat_row, seat_col=t.seat_col) for t in r.tickets],
        )
        for r in rows
    ]


@router.post("/{reservation_id}/approve", response_model=ReservationOut)
def approve_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.status != ReservationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can approve only pending reservations")

    r.status = ReservationStatus.CONFIRMED
    db.commit()
    db.refresh(r)

    return ReservationOut(
        id=r.id,
        status=r.status,
        screening_id=r.screening_id,
        user_id=r.user_id,
        created_at=r.created_at,
        notes=r.notes,
        tickets=[ReservationTicketOut(seat_row=t.seat_row, seat_col=t.seat_col) for t in r.tickets],
    )


@router.post("/{reservation_id}/decline", response_model=ReservationOut)
def decline_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.status in (ReservationStatus.CANCELED, ReservationStatus.COMPLETED):
        raise HTTPException(status_code=400, detail="Cannot decline in this status")

    r.status = ReservationStatus.CANCELED
    db.commit()
    db.refresh(r)

    return ReservationOut(
        id=r.id,
        status=r.status,
        screening_id=r.screening_id,
        user_id=r.user_id,
        created_at=r.created_at,
        notes=r.notes,
        tickets=[ReservationTicketOut(seat_row=t.seat_row, seat_col=t.seat_col) for t in r.tickets],
    )
