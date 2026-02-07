from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User, UserRole
from app.core.security import hash_password


def ensure_admin(db: Session) -> None:
    # един админ профил при създаване на платформата
    admin = db.scalar(select(User).where(User.role == UserRole.ADMIN))
    if admin:
        return

    admin_user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=hash_password("admin1234"),
        role=UserRole.ADMIN,
    )
    db.add(admin_user)
    db.commit()
