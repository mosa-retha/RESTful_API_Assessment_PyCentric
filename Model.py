from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    name: str
    email: EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str