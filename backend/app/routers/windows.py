from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.window import Window
from app.models.canteen import Canteen
from app.models.dish import Dish
from app.schemas.window import WindowCreate, WindowUpdate, WindowOut, WindowListOut
from app.schemas.common import PaginatedResponse
from typing import Optional
from uuid import UUID
import math

router = APIRouter(prefix="/windows", tags=["窗口"])


@router.get("", response_model=PaginatedResponse[WindowListOut])
async def list_windows(
    canteen_id: Optional[UUID] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取窗口列表，支持筛选"""
    conditions = []
    if canteen_id:
        conditions.append(Window.canteen_id == canteen_id)
    if category:
        conditions.append(Window.category == category)
    if is_active is not None:
        conditions.append(Window.is_active == is_active)

    count_q = select(func.count(Window.id)).where(*conditions)
    total = (await db.execute(count_q)).scalar()

    q = select(Window, Canteen.name).join(Canteen).where(*conditions)
    # Filter by payment method in Python (JSON array check)
    if payment_method:
        q = q.where(Window.payment_methods.contains([payment_method]))

    q = q.order_by(Window.avg_rating.desc().nullslast())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    rows = result.all()

    items = []
    for window, canteen_name in rows:
        d_count_q = select(func.count(Dish.id)).where(Dish.window_id == window.id)
        d_count = (await db.execute(d_count_q)).scalar()
        items.append(WindowListOut(
            id=window.id, canteen_id=window.canteen_id, canteen_name=canteen_name,
            name=window.name, window_number=window.window_number,
            category=window.category, payment_methods=window.payment_methods,
            avg_rating=window.avg_rating, rating_count=window.rating_count,
            is_active=window.is_active, image_url=window.image_url,
            dish_count=d_count or 0
        ))

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size))
    )


@router.get("/{window_id}", response_model=WindowOut)
async def get_window(window_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取窗口详情"""
    q = select(Window, Canteen.name).join(Canteen).where(Window.id == window_id)
    result = await db.execute(q)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="窗口不存在")

    window, canteen_name = row
    d_count_q = select(func.count(Dish.id)).where(Dish.window_id == window.id)
    d_count = (await db.execute(d_count_q)).scalar()

    return WindowOut(
        id=window.id, canteen_id=window.canteen_id, canteen_name=canteen_name,
        name=window.name, window_number=window.window_number,
        category=window.category, payment_methods=window.payment_methods,
        avg_rating=window.avg_rating, rating_count=window.rating_count,
        is_active=window.is_active, image_url=window.image_url,
        description=window.description, dish_count=d_count or 0,
        created_at=window.created_at, updated_at=window.updated_at,
    )


@router.get("/{window_id}/dishes")
async def get_window_dishes(
    window_id: UUID,
    category: Optional[str] = None,
    is_available: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取窗口的所有菜品"""
    from app.schemas.dish import DishListOut

    conditions = [Dish.window_id == window_id]
    if category:
        conditions.append(Dish.category == category)
    if is_available is not None:
        conditions.append(Dish.is_available == is_available)

    count_q = select(func.count(Dish.id)).where(*conditions)
    total = (await db.execute(count_q)).scalar()

    q = (select(Dish, Window.name, Canteen.name)
         .select_from(Dish)
         .join(Window).join(Canteen)
         .where(*conditions)
         .order_by(Dish.category, Dish.name)
         .offset((page - 1) * page_size).limit(page_size))
    result = await db.execute(q)
    rows = result.all()

    items = [
        DishListOut(
            id=d.id, window_id=d.window_id, window_name=wn, canteen_name=cn,
            name=d.name, category=d.category, price=float(d.price), unit=d.unit,
            image_url=d.image_url, nutrition=d.nutrition,
            is_available=d.is_available, is_recommended=d.is_recommended,
            avg_rating=d.avg_rating, rating_count=d.rating_count,
        )
        for d, wn, cn in rows
    ]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size))
    )
