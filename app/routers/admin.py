from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.deps import get_db, require_role
from app.models.user import User, UserRole
from app.models.cinema import Movie, Hall, Screening
from app.models.reservation import Reservation, ReservationTicket, ReservationStatus
from app.schemas.reservation import ReservationOut, ReservationTicketOut
from app.models.review import Review
from app.models.favorite import FavoriteMovie
from app.schemas.user import UserOut, UserRoleUpdateIn

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> list[UserOut]:
    rows = db.query(User).order_by(User.id.asc()).offset(skip).limit(min(limit, 100)).all()
    return [UserOut(id=u.id, email=u.email, username=u.username, role=u.role) for u in rows]


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> UserOut:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=u.id, email=u.email, username=u.username, role=u.role)


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdateIn,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.ADMIN)),
) -> UserOut:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    if u.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    if payload.role == UserRole.ADMIN or u.role == UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Admin role cannot be assigned/changed via API")

    u.role = payload.role
    db.commit()
    db.refresh(u)
    return UserOut(id=u.id, email=u.email, username=u.username, role=u.role)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.ADMIN)),
) -> dict[str, bool]:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    if u.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    if u.role == UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Admin user cannot be deleted via API")

    db.query(FavoriteMovie).filter(FavoriteMovie.user_id == user_id).delete()

    db.query(Review).filter(Review.user_id == user_id).delete()

    reservations = db.query(Reservation).filter(Reservation.user_id == user_id).all()
    for r in reservations:
        db.query(ReservationTicket).filter(ReservationTicket.reservation_id == r.id).delete()
        db.delete(r)

    db.delete(u)
    db.commit()
    return {"ok": True}


@router.delete("/reservations/{reservation_id}")
def admin_delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> dict[str, bool]:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    db.query(ReservationTicket).filter(ReservationTicket.reservation_id == reservation_id).delete()
    db.delete(r)
    db.commit()
    return {"ok": True}


@router.post("/reservations/{reservation_id}/confirm", response_model=ReservationOut)
def admin_confirm_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.status != ReservationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can confirm only pending reservations")

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


@router.post("/reservations/{reservation_id}/complete", response_model=ReservationOut)
def admin_complete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> ReservationOut:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r.status == ReservationStatus.CANCELED:
        raise HTTPException(status_code=400, detail="Canceled reservations cannot be completed")

    if r.status != ReservationStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Can complete only confirmed reservations")

    r.status = ReservationStatus.COMPLETED
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


@router.delete("/movies/{movie_id}")
def admin_delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> dict[str, bool]:
    m = db.get(Movie, movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found")

    has_screenings = db.query(Screening.id).filter(Screening.movie_id == movie_id).first() is not None
    if has_screenings:
        raise HTTPException(status_code=400, detail="Cannot delete movie with screenings")

    db.query(Review).filter(Review.movie_id == movie_id).delete()
    db.query(FavoriteMovie).filter(FavoriteMovie.movie_id == movie_id).delete()

    db.delete(m)
    db.commit()
    return {"ok": True}


@router.delete("/halls/{hall_id}")
def admin_delete_hall(
    hall_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> dict[str, bool]:
    h = db.get(Hall, hall_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hall not found")

    has_screenings = db.query(Screening.id).filter(Screening.hall_id == hall_id).first() is not None
    if has_screenings:
        raise HTTPException(status_code=400, detail="Cannot delete hall with screenings")

    db.delete(h)
    db.commit()
    return {"ok": True}


@router.delete("/screenings/{screening_id}")
def admin_delete_screening(
    screening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> dict[str, bool]:
    s = db.get(Screening, screening_id)
    if not s:
        raise HTTPException(status_code=404, detail="Screening not found")

    has_reservations = db.query(Reservation.id).filter(Reservation.screening_id == screening_id).first() is not None
    if has_reservations:
        raise HTTPException(status_code=400, detail="Cannot delete screening with reservations")

    db.delete(s)
    db.commit()
    return {"ok": True}
