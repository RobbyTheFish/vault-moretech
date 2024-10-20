# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.auth import BearerAuthenticationStrategy, Authenticator
from auth.models import User
from bson import ObjectId
from typing import Optional

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    strategy = BearerAuthenticationStrategy()
    authenticator = Authenticator(strategy)
    try:
        user = await authenticator.authenticate(token=token)
        return user
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
