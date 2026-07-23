import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Profile / preferences
    profile: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    # e.g. { "goals": [], "skills": [], "timezone": "UTC", "language": "en", "voice": "alloy" }

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="user", lazy="dynamic")
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="user", lazy="dynamic")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="user", lazy="dynamic")
