from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, nullable=False)
    secret_key = Column(String, nullable=False, unique=True)
    secret_value = Column(LargeBinary, nullable=False)
    is_deleted = Column(Boolean, default=False)
    is_destoyed = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f"<Secret(key={self.secret_key}, value={self.secret_value})>"
