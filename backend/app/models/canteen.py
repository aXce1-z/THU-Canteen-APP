import uuid
from datetime import datetime
from sqlalchemy import String, Float, Text, DateTime, func, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Canteen(Base):
    __tablename__ = "canteens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="食堂名称")
    location: Mapped[str] = mapped_column(String(200), nullable=True, comment="位置描述")
    latitude: Mapped[float] = mapped_column(Float, nullable=True, comment="纬度")
    longitude: Mapped[float] = mapped_column(Float, nullable=True, comment="经度")
    opening_hours: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="营业时间")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="食堂图片")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="简介")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    windows: Mapped[list["Window"]] = relationship(
        "Window", back_populates="canteen", cascade="all, delete-orphan"
    )
