from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, LargeBinary
from sqlalchemy.orm import relationship
from auth.db import Base
from passlib.hash import bcrypt
import uuid
from datetime import datetime
import enum
from uuid import UUID


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_group_roles = relationship("UserGroupRole", back_populates="user")

    def verify_password(self, password):
        return bcrypt.verify(password, self.hashed_password)


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )  # Сохраняем UUID как строку
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_group_roles = relationship("UserGroupRole", back_populates="group")
    applications = relationship("Application", back_populates="group")


class RoleEnum(enum.Enum):
    admin = "admin"
    engineer = "engineer"


class UserGroupRole(Base):
    __tablename__ = "user_group_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    role = Column(Enum(RoleEnum))

    user = relationship("User", back_populates="user_group_roles")
    group = relationship("Group", back_populates="user_group_roles")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )  # Сохраняем UUID как строку
    name = Column(String, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="applications")
    type_strategies_encrypts = relationship(
        "TypeStrategiesEncrypt", back_populates="applications"
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    master_token = Column(String, unique=True, index=True)

    def __init__(self, name):
        self.name = name
        self.master_token = str(uuid.uuid4())

    tokens = relationship("Token", back_populates="roles")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    access_token = Column(String, unique=True, index=True)
    refresh_token = Column(String, unique=True, index=True)
    access_token_expires_at = Column(DateTime)
    refresh_token_expires_at = Column(DateTime)

    roles = relationship("Role", back_populates="tokens")


class TypeStrategiesEncrypt(Base):
    __tablename__ = "type_strategies_encrypts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    app_key = Column(LargeBinary)
    application_uuid = Column(String, ForeignKey("applications.uuid"))

    applications = relationship(
        "Application", back_populates="type_strategies_encrypts"
    )
