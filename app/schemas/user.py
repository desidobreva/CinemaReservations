from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole


class UserRoleUpdateIn(BaseModel):
    role: UserRole
