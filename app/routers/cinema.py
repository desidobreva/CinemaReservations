from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.deps import get_db, require_role
from app.models.user import User, UserRole
from app.models.cinema import Movie, Hall, Screening
from app.models.reservation import Reservation
from app.schemas.cinema import (
    MovieCreateIn, MovieOut, MovieUpdateIn,
    HallCreateIn, HallOut, HallUpdateIn,
    ScreeningCreateIn, ScreeningOut, ScreeningUpdateIn
)

router = APIRouter(prefix="/cinema", tags=["cinema"])


# ---------------- MOVIES ----------------
@router.get("/movies", response_model=list[MovieOut])
def list_movies(
    db: Session = Depends(get_db),
    query: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=100),
) -> list[MovieOut]:
    q = db.query(Movie)
    if query:
        q = q.filter(Movie.title.ilike(f"%{query}%"))
    if category:
        q = q.filter(Movie.category == category)
    rows = q.order_by(Movie.id.desc()).all()
    return [MovieOut(id=m.id, title=m.title, description=m.description, category=m.category) for m in rows]


@router.get("/movies/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieOut:
    m = db.get(Movie, movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found")
    return MovieOut(id=m.id, title=m.title, description=m.description, category=m.category)


@router.post("/movies", response_model=MovieOut)
def create_movie(
    payload: MovieCreateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> MovieOut:
    m = Movie(title=payload.title, description=payload.description, category=payload.category)
    db.add(m)
    db.commit()
    db.refresh(m)
    return MovieOut(id=m.id, title=m.title, description=m.description, category=m.category)


@router.put("/movies/{movie_id}", response_model=MovieOut)
def update_movie(
    movie_id: int,
    payload: MovieUpdateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> MovieOut:
    m = db.get(Movie, movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found")

    if payload.title is not None:
        m.title = payload.title
    if payload.description is not None:
        m.description = payload.description
    if payload.category is not None:
        m.category = payload.category

    db.commit()
    db.refresh(m)
    return MovieOut(id=m.id, title=m.title, description=m.description, category=m.category)


@router.delete("/movies/{movie_id}")
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    m = db.get(Movie, movie_id)
    if not m:
        raise HTTPException(status_code=404, detail="Movie not found")

    # пазим целостта: ако има прожекции -> не трием
    has_screenings = db.query(Screening.id).filter(Screening.movie_id == movie_id).first() is not None
    if has_screenings:
        raise HTTPException(status_code=400, detail="Cannot delete movie with screenings")

    db.delete(m)
    db.commit()
    return {"ok": True}


# ---------------- HALLS ----------------
@router.get("/halls", response_model=list[HallOut])
def list_halls(db: Session = Depends(get_db)) -> list[HallOut]:
    rows = db.query(Hall).order_by(Hall.id.asc()).all()
    return [HallOut(id=h.id, name=h.name, rows=h.rows, cols=h.cols) for h in rows]


@router.get("/halls/{hall_id}", response_model=HallOut)
def get_hall(hall_id: int, db: Session = Depends(get_db)) -> HallOut:
    h = db.get(Hall, hall_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hall not found")
    return HallOut(id=h.id, name=h.name, rows=h.rows, cols=h.cols)


@router.post("/halls", response_model=HallOut)
def create_hall(
    payload: HallCreateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> HallOut:
    exists = db.query(Hall).filter(Hall.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Hall name already exists")

    h = Hall(name=payload.name, rows=payload.rows, cols=payload.cols)
    db.add(h)
    db.commit()
    db.refresh(h)
    return HallOut(id=h.id, name=h.name, rows=h.rows, cols=h.cols)


@router.put("/halls/{hall_id}", response_model=HallOut)
def update_hall(
    hall_id: int,
    payload: HallUpdateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> HallOut:
    h = db.get(Hall, hall_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hall not found")

    # ако се опитваме да сменим rows/cols, не позволяваме ако има прожекции/резервации
    changing_size = (payload.rows is not None) or (payload.cols is not None)
    if changing_size:
        has_screenings = db.query(Screening.id).filter(Screening.hall_id == hall_id).first() is not None
        if has_screenings:
            raise HTTPException(status_code=400, detail="Cannot resize hall with screenings (seat layout would break)")

    if payload.name is not None:
        # уникално име
        exists = db.query(Hall).filter(Hall.name == payload.name, Hall.id != hall_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="Hall name already exists")
        h.name = payload.name
    if payload.rows is not None:
        h.rows = payload.rows
    if payload.cols is not None:
        h.cols = payload.cols

    db.commit()
    db.refresh(h)
    return HallOut(id=h.id, name=h.name, rows=h.rows, cols=h.cols)


@router.delete("/halls/{hall_id}")
def delete_hall(
    hall_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
) -> dict:
    h = db.get(Hall, hall_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hall not found")

    has_screenings = db.query(Screening.id).filter(Screening.hall_id == hall_id).first() is not None
    if has_screenings:
        raise HTTPException(status_code=400, detail="Cannot delete hall with screenings")

    db.delete(h)
    db.commit()
    return {"ok": True}


# ---------------- SCREENINGS ----------------
@router.get("/screenings", response_model=list[ScreeningOut])
def list_screenings(
    db: Session = Depends(get_db),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    movie_id: int | None = None,
    hall_id: int | None = None,
) -> list[ScreeningOut]:
    q = db.query(Screening)
    filters = []
    if date_from is not None:
        filters.append(Screening.starts_at >= date_from)
    if date_to is not None:
        filters.append(Screening.starts_at <= date_to)
    if movie_id is not None:
        filters.append(Screening.movie_id == movie_id)
    if hall_id is not None:
        filters.append(Screening.hall_id == hall_id)
    if filters:
        q = q.filter(and_(*filters))

    rows = q.order_by(Screening.starts_at.asc()).all()
    return [
        ScreeningOut(id=s.id, movie_id=s.movie_id, hall_id=s.hall_id, starts_at=s.starts_at, provider_id=s.provider_id)
        for s in rows
    ]


@router.get("/screenings/{screening_id}", response_model=ScreeningOut)
def get_screening(screening_id: int, db: Session = Depends(get_db)) -> ScreeningOut:
    s = db.get(Screening, screening_id)
    if not s:
        raise HTTPException(status_code=404, detail="Screening not found")
    return ScreeningOut(id=s.id, movie_id=s.movie_id, hall_id=s.hall_id, starts_at=s.starts_at, provider_id=s.provider_id)


@router.post("/screenings", response_model=ScreeningOut)
def create_screening(
    payload: ScreeningCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> ScreeningOut:
    if not db.get(Movie, payload.movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")
    if not db.get(Hall, payload.hall_id):
        raise HTTPException(status_code=404, detail="Hall not found")

    s = Screening(movie_id=payload.movie_id, hall_id=payload.hall_id, starts_at=payload.starts_at, provider_id=user.id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return ScreeningOut(id=s.id, movie_id=s.movie_id, hall_id=s.hall_id, starts_at=s.starts_at, provider_id=s.provider_id)


@router.put("/screenings/{screening_id}", response_model=ScreeningOut)
def update_screening(
    screening_id: int,
    payload: ScreeningUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> ScreeningOut:
    s = db.get(Screening, screening_id)
    if not s:
        raise HTTPException(status_code=404, detail="Screening not found")

    # provider може да редактира само свои прожекции (admin може всичко)
    if user.role != UserRole.ADMIN and s.provider_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ако има резервации, не позволяваме смяна на hall_id/movie_id (за да не се чупят)
    has_reservations = db.query(Reservation.id).filter(Reservation.screening_id == screening_id).first() is not None
    if has_reservations and (payload.hall_id is not None or payload.movie_id is not None):
        raise HTTPException(status_code=400, detail="Cannot change hall/movie when reservations exist")

    if payload.movie_id is not None:
        if not db.get(Movie, payload.movie_id):
            raise HTTPException(status_code=404, detail="Movie not found")
        s.movie_id = payload.movie_id

    if payload.hall_id is not None:
        if not db.get(Hall, payload.hall_id):
            raise HTTPException(status_code=404, detail="Hall not found")
        s.hall_id = payload.hall_id

    if payload.starts_at is not None:
        s.starts_at = payload.starts_at

    db.commit()
    db.refresh(s)
    return ScreeningOut(id=s.id, movie_id=s.movie_id, hall_id=s.hall_id, starts_at=s.starts_at, provider_id=s.provider_id)


@router.delete("/screenings/{screening_id}")
def delete_screening(
    screening_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
) -> dict:
    s = db.get(Screening, screening_id)
    if not s:
        raise HTTPException(status_code=404, detail="Screening not found")

    if user.role != UserRole.ADMIN and s.provider_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    has_reservations = db.query(Reservation.id).filter(Reservation.screening_id == screening_id).first() is not None
    if has_reservations:
        raise HTTPException(status_code=400, detail="Cannot delete screening with reservations")

    db.delete(s)
    db.commit()
    return {"ok": True}
