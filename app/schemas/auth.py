from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginIn(BaseModel):
    username_or_email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
