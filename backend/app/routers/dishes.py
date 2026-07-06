from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.dish import Dish
from app.models.window import Window
from app.models.canteen import Canteen
from app.schemas.dish import DishCreate, DishUpdate, DishOut, DishListOut, NutritionOut
from app.schemas.common import PaginatedResponse
from typing import Optional
from uuid import UUID
import math

router = APIRouter(prefix="/dishes", tags=["菜品"])


@router.get("", response_model=PaginatedResponse[DishListOut])
async def list_dishes(
    window_id: Optional[UUID] = None,
    category: Optional[str] = None,
    is_available: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取菜品列表"""
    conditions = []
    if window_id:
        conditions.append(Dish.window_id == window_id)
    if category:
        conditions.append(Dish.category == category)
    if is_available is not None:
        conditions.append(Dish.is_available == is_available)
    if min_price is not None:
        conditions.append(Dish.price >= min_price)
    if max_price is not None:
        conditions.append(Dish.price <= max_price)

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


@router.get("/hot", response_model=list[DishListOut])
async def get_hot_dishes(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """获取热门菜品（按评分和评价数排序）"""
    q = (select(Dish, Window.name, Canteen.name)
         .select_from(Dish)
         .join(Window).join(Canteen)
         .where(Dish.is_available == True, Dish.rating_count > 0)
         .order_by(Dish.avg_rating.desc(), Dish.rating_count.desc())
         .limit(limit))
    result = await db.execute(q)
    rows = result.all()

    return [
        DishListOut(
            id=d.id, window_id=d.window_id, window_name=wn, canteen_name=cn,
            name=d.name, category=d.category, price=float(d.price), unit=d.unit,
            image_url=d.image_url, nutrition=d.nutrition,
            is_available=d.is_available, is_recommended=d.is_recommended,
            avg_rating=d.avg_rating, rating_count=d.rating_count,
        )
        for d, wn, cn in rows
    ]


@router.get("/{dish_id}", response_model=DishOut)
async def get_dish(dish_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取菜品详情"""
    q = (select(Dish, Window.name, Window.id, Canteen.id, Canteen.name)
         .select_from(Dish)
         .join(Window).join(Canteen)
         .where(Dish.id == dish_id))
    result = await db.execute(q)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="菜品不存在")

    d, wn, wid, cid, cn = row
    return DishOut(
        id=d.id, window_id=d.window_id, window_name=wn,
        canteen_id=cid, canteen_name=cn,
        name=d.name, category=d.category, price=float(d.price), unit=d.unit,
        image_url=d.image_url, nutrition=d.nutrition,
        is_available=d.is_available, is_recommended=d.is_recommended,
        avg_rating=d.avg_rating, rating_count=d.rating_count,
        created_at=d.created_at, updated_at=d.updated_at,
    )


@router.get("/{dish_id}/nutrition", response_model=NutritionOut)
async def get_dish_nutrition(dish_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取菜品营养成分"""
    q = select(Dish.nutrition).where(Dish.id == dish_id)
    result = await db.execute(q)
    nutrition = result.scalar_one_or_none()

    if not nutrition:
        return NutritionOut()

    return NutritionOut(**nutrition)
