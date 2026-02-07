# app/routers/users.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


class UserMeUpdateIn(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, username=user.username, role=user.role)


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserMeUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    # ако user прати празно тяло -> нищо не променяме
    if payload.email is None and payload.username is None and payload.password is None:
        raise HTTPException(status_code=400, detail="No fields provided")

    # уникалност: email / username
    if payload.email is not None:
        exists = (
            db.query(User)
            .filter(User.email == str(payload.email), User.id != user.id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = str(payload.email)

    if payload.username is not None:
        exists = (
            db.query(User)
            .filter(User.username == payload.username, User.id != user.id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Username already in use")
        user.username = payload.username

    if payload.password is not None:
        if len(payload.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(user)

    return UserOut(id=user.id, email=user.email, username=user.username, role=user.role)
