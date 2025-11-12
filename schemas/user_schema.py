from sqlmodel import SQLModel
from pydantic import EmailStr, field_validator
from typing import Optional

class LoginSchema(SQLModel):
    email: EmailStr
    password: str

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(SQLModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserPublic(SQLModel):
    id: int
    email: EmailStr

class UserReadSchema(SQLModel):
    id: int  # Add this field - it's essential for the assignment
    name: str
    email: EmailStr
    role: Optional[str] = None  # Add role if you want to display it in the dropdown