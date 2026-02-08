from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.reservation import ReservationCreateIn, ReservationOut, ReservationTicketOut
from app.services.reservation_service import create_reservation
from app.schemas.reservation import ConfirmPaymentIn
from app.models.cinema import Screening
from app.schemas.reservation import ReservationRescheduleIn

router = APIRouter(prefix="/reservations", tags=["reservations"])


def to_out(r: Reservation) -> ReservationOut:
    return ReservationOut(
        id=r.id,
        status=r.status,
        screening_id=r.screening_id,
        user_id=r.user_id,
        created_at=r.created_at,
        notes=r.notes,
        tickets=[ReservationTicketOut(seat_row=t.seat_row, seat_col=t.seat_col) for t in r.tickets],
    )


@router.post("", response_model=ReservationOut)
def create_my_reservation(
    payload: ReservationCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.USER, UserRole.PROVIDER, UserRole.ADMIN)),
) -> ReservationOut:
    r = create_reservation(db, user, payload)
    return to_out(r)


@router.get("/me", response_model=list[ReservationOut])
def list_my_reservations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReservationOut]:
    rows = db.query(Reservation).filter(Reservation.user_id == user.id).order_by(Reservation.id.desc()).all()
    return [to_out(r) for r in rows]


@router.get("/{reservation_id}", response_model=ReservationOut)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.user_id != user.id and user.role not in (UserRole.PROVIDER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not allowed")

    return to_out(r)


@router.post("/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.user_id != user.id and user.role not in (UserRole.PROVIDER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not allowed")

    if r.status in (ReservationStatus.CANCELED, ReservationStatus.COMPLETED):
        raise HTTPException(status_code=400, detail="Cannot cancel in this status")

    r.tickets.clear()
    r.status = ReservationStatus.CANCELED

    db.commit()
    db.refresh(r)

    return to_out(r)

@router.post("/{reservation_id}/confirm", response_model=ReservationOut)
def confirm_reservation_payment(
    reservation_id: int,
    payload: ConfirmPaymentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.user_id != user.id and user.role not in (UserRole.PROVIDER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not allowed")

    if r.status != ReservationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Reservation is not pending")

    screening: Screening | None = db.get(Screening, r.screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    now = datetime.now(timezone.utc)
    screening_time = screening.starts_at
    if screening_time.tzinfo is None:
        screening_time = screening_time.replace(tzinfo=timezone.utc)
    if screening_time <= now:
        raise HTTPException(status_code=400, detail="Screening already started")

    r.status = ReservationStatus.CONFIRMED
    db.commit()
    db.refresh(r)

    return to_out(r)

@router.post("/{reservation_id}/reschedule", response_model=ReservationOut)
def reschedule_reservation(
    reservation_id: int,
    payload: ReservationRescheduleIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.user_id != user.id and user.role not in (UserRole.PROVIDER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not allowed")

    if r.status == ReservationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot reschedule completed reservation")

    r.tickets.clear() 
    r.status = ReservationStatus.CANCELED
    db.commit()
    db.refresh(r)

    new_data = ReservationCreateIn(
        screening_id=payload.new_screening_id,
        seats=payload.seats,
        notes=payload.notes,
    )
    new_r = create_reservation(db, user, new_data)

    return to_out(new_r)