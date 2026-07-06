import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

import enum


class UserRole(str, enum.Enum):
    USER = "user"
    VOLUNTEER = "volunteer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    openid: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="微信OpenID"
    )
    nickname: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="昵称"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="头像URL"
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), default=UserRole.USER, comment="角色"
    )
    contribution_points: Mapped[int] = mapped_column(
        Integer, default=0, comment="贡献积分"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )
    change_logs: Mapped[list["ChangeLog"]] = relationship(
        "ChangeLog", back_populates="user", cascade="all, delete-orphan"
    )
