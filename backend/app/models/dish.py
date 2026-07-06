import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, Numeric, func, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    window_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("windows.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属窗口",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="菜品名称")
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="分类: 主食/炒菜/小吃/汤粥/饮品"
    )
    price: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=0, comment="价格"
    )
    unit: Mapped[str] = mapped_column(
        String(20), default="份", comment="单位: 份/碗/两/个"
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="菜品图片")
    nutrition: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='营养成分: {calories, protein, fat, carbs, fiber, sodium}',
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="当前是否供应"
    )
    is_recommended: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否推荐菜"
    )
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    window: Mapped["Window"] = relationship("Window", back_populates="dishes")
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="dish", cascade="all, delete-orphan"
    )
