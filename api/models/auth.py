from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    name: str = Field(..., example="John Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., min_length=8, example="strongpassword")

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": "strongpassword"
            }
        }
    )


class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="strongpassword")

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "password": "strongpassword"
            }
        }
    )


class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = ConfigDict(
        schema_extra={
            "example": {
                "access_token": "jwt.token.here",
                "token_type": "bearer"
            }
        }
    )


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr

    model_config = ConfigDict(
        orm_mode=True,
        schema_extra={
            "example": {
                "id": "60c72b2f9b1d4e3a5c8e4b7a",
                "name": "John Doe",
                "email": "john.doe@example.com"
            }
        }
    )

