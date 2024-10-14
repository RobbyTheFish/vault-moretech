from fastapi import APIRouter, Depends, HTTPException, status
from api.models.auth import UserRegisterRequest, UserLoginRequest, TokenResponse
from auth.auth_manager import AuthManager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.token_utils import create_access_token, create_refresh_token
from auth.db import AsyncSessionLocal
from auth.models import User
from sqlalchemy.future import select

router = APIRouter()
auth_manager = AuthManager()
security = HTTPBearer()

@router.post("/register", response_model=TokenResponse)
async def register_user(request: UserRegisterRequest):
    async with AsyncSessionLocal() as session:
        # Проверяем уникальность username
        result = await session.execute(select(User).where(User.username == request.username))
        existing_user_by_username = result.scalars().first()
        if existing_user_by_username:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Проверяем уникальность email
        result = await session.execute(select(User).where(User.email == request.email))
        existing_user_by_email = result.scalars().first()
        if existing_user_by_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Создание нового пользователя с хешированным паролем
        hashed_password = auth_manager.hash_password(request.password)
        new_user = User(username=request.username, email=request.email, hashed_password=hashed_password)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        # Генерация токенов
        access_token = auth_manager.create_access_token(new_user.id)
        return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
async def login_user(request: UserLoginRequest):
    user = await auth_manager.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Генерация токена
    access_token = auth_manager.create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer"}