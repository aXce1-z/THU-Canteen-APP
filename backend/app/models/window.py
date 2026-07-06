import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, Integer, func, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Window(Base):
    __tablename__ = "windows"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    canteen_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("canteens.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属食堂",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="窗口名称")
    window_number: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="窗口编号"
    )
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="窗口分类"
    )
    payment_methods: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=lambda: ["campus_card"],
        comment='支持的支付方式: campus_card, wechat, alipay'
    )
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0, comment="平均评分")
    rating_count: Mapped[int] = mapped_column(Integer, default=0, comment="评价数量")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否营业中")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="窗口简介")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    canteen: Mapped["Canteen"] = relationship("Canteen", back_populates="windows")
    dishes: Mapped[list["Dish"]] = relationship(
        "Dish", back_populates="window", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="window", cascade="all, delete-orphan"
    )
