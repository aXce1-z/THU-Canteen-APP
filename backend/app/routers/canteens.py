from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.canteen import Canteen
from app.models.window import Window
from app.models.dish import Dish
from app.schemas.canteen import CanteenCreate, CanteenUpdate, CanteenOut, CanteenListOut
from app.schemas.common import PaginatedResponse
from typing import Optional
from uuid import UUID
import math

router = APIRouter(prefix="/canteens", tags=["食堂"])


@router.get("", response_model=PaginatedResponse[CanteenListOut])
async def list_canteens(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取食堂列表"""
    # Count total
    count_q = select(func.count(Canteen.id))
    total = (await db.execute(count_q)).scalar()

    # Get canteens with window counts
    q = select(Canteen).order_by(Canteen.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    canteens = result.scalars().all()

    items = []
    for c in canteens:
        w_count_q = select(func.count(Window.id)).where(Window.canteen_id == c.id)
        w_count = (await db.execute(w_count_q)).scalar()
        items.append(CanteenListOut(
            id=c.id, name=c.name, location=c.location,
            image_url=c.image_url, window_count=w_count or 0
        ))

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size))
    )


@router.get("/{canteen_id}", response_model=CanteenOut)
async def get_canteen(canteen_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取食堂详情"""
    q = select(Canteen).where(Canteen.id == canteen_id)
    result = await db.execute(q)
    canteen = result.scalar_one_or_none()
    if not canteen:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="食堂不存在")

    w_count_q = select(func.count(Window.id)).where(Window.canteen_id == canteen.id)
    w_count = (await db.execute(w_count_q)).scalar()

    return CanteenOut(
        id=canteen.id, name=canteen.name, location=canteen.location,
        latitude=canteen.latitude, longitude=canteen.longitude,
        opening_hours=canteen.opening_hours, image_url=canteen.image_url,
        description=canteen.description, window_count=w_count or 0,
        created_at=canteen.created_at, updated_at=canteen.updated_at
    )


@router.get("/{canteen_id}/windows")
async def get_canteen_windows(
    canteen_id: UUID,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取食堂的所有窗口"""
    from app.schemas.window import WindowListOut

    conditions = [Window.canteen_id == canteen_id]
    if category:
        conditions.append(Window.category == category)
    if is_active is not None:
        conditions.append(Window.is_active == is_active)

    count_q = select(func.count(Window.id)).where(*conditions)
    total = (await db.execute(count_q)).scalar()

    q = select(Window, Canteen.name).join(Canteen).where(*conditions)
    q = q.order_by(Window.name).offset((page - 1) * page_size).limit(page_size)
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
