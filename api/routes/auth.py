from datetime import datetime, timedelta

import jwt
from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, status
from passlib.context import CryptContext

from api.models.auth import Token, UserCreate, UserLogin, UserResponse
from auth.config import JWT_ALGORITHM, JWT_SECRET
from auth.db import db
from auth.dependencies import get_current_user
from auth.models import User

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(*, data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return UserResponse(
        id=str(created_user["_id"]),
        name=created_user["name"],
        email=created_user["email"],
    )


@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(db_user["_id"])}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/update-password", response_model=UserResponse)
async def update_password(
    current_user: User = Depends(get_current_user),
    old_password: str = Body(..., embed=True, example="oldpassword"),
    new_password: str = Body(..., embed=True, min_length=8, example="newstrongpassword"),
):
    if not verify_password(old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    hashed_new_password = get_password_hash(new_password)
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"password": hashed_new_password}},
    )
    updated_user = await db.users.find_one({"_id": ObjectId(current_user.id)})
    return UserResponse(
        id=str(updated_user["_id"]),
        name=updated_user["name"],
        email=updated_user["email"],
    )


@router.delete("/delete-user", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(current_user: User = Depends(get_current_user)):
    await db.users.delete_one({"_id": ObjectId(current_user.id)})
    return
