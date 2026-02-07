from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.deps import get_db, get_current_user
from app.models.favorite import FavoriteMovie
from app.models.cinema import Movie
from app.models.user import User
from app.schemas.favorite import FavoriteOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/movies", response_model=list[FavoriteOut])
def list_favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[FavoriteOut]:
    rows = db.query(FavoriteMovie).filter(FavoriteMovie.user_id == user.id).order_by(FavoriteMovie.id.desc()).all()
    return [FavoriteOut(id=f.id, user_id=f.user_id, movie_id=f.movie_id) for f in rows]


@router.post("/movies/{movie_id}", response_model=FavoriteOut)
def add_favorite(movie_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> FavoriteOut:
    if not db.get(Movie, movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")

    fav = FavoriteMovie(user_id=user.id, movie_id=movie_id)
    db.add(fav)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already in favorites")
    db.refresh(fav)
    return FavoriteOut(id=fav.id, user_id=fav.user_id, movie_id=fav.movie_id)


@router.delete("/movies/{movie_id}")
def remove_favorite(movie_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    fav = db.query(FavoriteMovie).filter(FavoriteMovie.user_id == user.id, FavoriteMovie.movie_id == movie_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Not in favorites")
    db.delete(fav)
    db.commit()
    return {"ok": True}
