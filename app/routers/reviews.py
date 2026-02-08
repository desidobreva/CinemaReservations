from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.review import Review
from app.models.cinema import Movie
from app.models.user import User
from app.schemas.review import ReviewCreateIn, ReviewOut

router = APIRouter(prefix="/movies", tags=["reviews"])


@router.get("/{movie_id}/reviews", response_model=list[ReviewOut])
def list_reviews(
    movie_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[ReviewOut]:
    if not db.get(Movie, movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")

    rows = db.query(Review).filter(Review.movie_id == movie_id).order_by(Review.id.desc()).offset(skip).limit(min(limit, 100)).all()
    return [ReviewOut(id=r.id, user_id=r.user_id, movie_id=r.movie_id, rating=r.rating, comment=r.comment) for r in rows]


@router.post("/{movie_id}/reviews", response_model=ReviewOut)
def create_review(
    movie_id: int,
    payload: ReviewCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewOut:
    if not db.get(Movie, movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")

    r = Review(user_id=user.id, movie_id=movie_id, rating=payload.rating, comment=payload.comment)
    db.add(r)
    db.commit()
    db.refresh(r)
    return ReviewOut(id=r.id, user_id=r.user_id, movie_id=r.movie_id, rating=r.rating, comment=r.comment)
