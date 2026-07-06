import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Boolean, func, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    dish_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("dishes.id", ondelete="SET NULL"),
        nullable=True,
    )
    window_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("windows.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False, comment="评分 1-5")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="评价内容")
    images: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment="图片URL数组"
    )
    tags: Mapped[list | None] = mapped_column(
        JSON, nullable=True,
        comment='标签: ["分量足", "偏辣", "排队快", "性价比高", ...]'
    )
    like_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数")
    is_approved: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="审核状态"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="reviews")
    window: Mapped["Window"] = relationship("Window", back_populates="reviews")
    dish: Mapped["Dish"] = relationship("Dish", back_populates="reviews")
