from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.user import User, UserRole
from app.models.reservation import Reservation, ReservationStatus
from app.models.cinema import Screening

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/complete-past-reservations")
def complete_past_reservations(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.PROVIDER)),
) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # намираме confirmed резервации, чиято прожекция е минала
    rows = (
        db.query(Reservation)
        .join(Screening, Reservation.screening_id == Screening.id)
        .filter(Reservation.status == ReservationStatus.CONFIRMED)
        .filter(Screening.starts_at < now)
        .all()
    )

    count = 0
    for r in rows:
        r.status = ReservationStatus.COMPLETED
        count += 1

    db.commit()
    return {"completed": count}
