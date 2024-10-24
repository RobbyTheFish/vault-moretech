# auth.py
from abc import ABC, abstractmethod

import jwt
from bson import ObjectId
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from ldap3 import ALL, Connection, Server

from auth.config import (
    JWT_ALGORITHM,
    JWT_SECRET,
    LDAP_BIND_DN,
    LDAP_SEARCH_BASE,
    LDAP_SERVER,
)
from auth.db import db
from auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthenticationStrategy(ABC):
    @abstractmethod
    async def authenticate(
        self, token: str | None = None, username: str | None = None, password: str | None = None
    ) -> User:
        pass


class BearerAuthenticationStrategy(AuthenticationStrategy):
    async def authenticate(
        self, token: str | None = None, username: str | None = None, password: str | None = None
    ) -> User:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        oid_userid = ObjectId(user_id)
        user = await db.users.find_one({"_id": oid_userid})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return User(**user)


class LDAPAuthenticationStrategy(AuthenticationStrategy):
    async def authenticate(
        self, token: str | None = None, username: str | None = None, password: str | None = None
    ) -> User:
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username and password required",
                headers={"WWW-Authenticate": "Basic"},
            )
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(
            server, user=f"{LDAP_BIND_DN}\\{username}", password=password, auto_bind=True
        )
        if not conn.bind():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="LDAP authentication failed",
                headers={"WWW-Authenticate": "Basic"},
            )
        conn.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter=f"(sAMAccountName={username})",
            attributes=["cn", "mail"],
        )
        if not conn.entries:
            raise HTTPException(status_code=404, detail="User not found in LDAP")
        entry = conn.entries[0]
        user = await db.users.find_one({"email": entry.mail.value})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found in database")
        return User(**user)


class Authenticator:
    def __init__(self, strategy: AuthenticationStrategy):
        self.strategy = strategy

    async def authenticate(
        self, token: str | None = None, username: str | None = None, password: str | None = None
    ) -> User:
        return await self.strategy.authenticate(token=token, username=username, password=password)
