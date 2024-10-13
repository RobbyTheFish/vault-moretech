from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from auth.db import Base
import uuid

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    master_token = Column(String, unique=True, index=True)

    def __init__(self, name):
        self.name = name
        self.master_token = str(uuid.uuid4())


    tokens = relationship("Token", back_populates="role")

class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'))
    access_token = Column(String, unique=True, index=True)
    refresh_token = Column(String, unique=True, index=True)
    access_token_expires_at = Column(DateTime)
    refresh_token_expires_at = Column(DateTime)

    role = relationship("Role", back_populates="tokens")