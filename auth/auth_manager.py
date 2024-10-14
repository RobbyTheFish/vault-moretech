from auth.models import User
from auth.db import AsyncSessionLocal
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from auth.config import Config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthManager:
    SECRET_KEY = Config.SECRET_KEY
    ALGORITHM = Config.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # время жизни access токена

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def authenticate_user(self, username: str, password: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            if user and self.verify_password(password, user.hashed_password):
                return user
            return None

    def create_access_token(self, user_id: int):
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"user_id": user_id, "exp": expire}
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.JWTError:
            return None
