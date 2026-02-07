from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.deps import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    exists = db.query(User).filter(or_(User.email == payload.email, User.username == payload.username)).first()
    if exists:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=str(payload.email),
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenOut:
    username_or_email = form_data.username
    password = form_data.password

    user = (
        db.query(User)
        .filter(or_(User.username == username_or_email, User.email == username_or_email))
        .first()
    )
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id))
    return TokenOut(access_token=token)
