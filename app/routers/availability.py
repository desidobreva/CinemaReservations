from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.cinema import Screening
from app.models.reservation import ReservationTicket

router = APIRouter(prefix="/screenings", tags=["availability"])


@router.get("/{screening_id}/availability")
def screening_availability(screening_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    screening = db.get(Screening, screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    hall = screening.hall
    taken = (
        db.query(ReservationTicket.seat_row, ReservationTicket.seat_col)
        .filter(ReservationTicket.screening_id == screening_id)
        .all()
    )
    return {
        "screening_id": screening_id,
        "hall": {"rows": hall.rows, "cols": hall.cols},
        "taken_seats": [{"seat_row": r, "seat_col": c} for (r, c) in taken],
    }
