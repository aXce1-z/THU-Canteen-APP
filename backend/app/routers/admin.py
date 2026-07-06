from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.canteen import Canteen
from app.models.window import Window
from app.models.dish import Dish
from app.models.user import User, UserRole
from app.schemas.canteen import CanteenCreate, CanteenUpdate, CanteenOut
from app.schemas.window import WindowCreate, WindowUpdate, WindowOut
from app.schemas.dish import DishCreate, DishUpdate, DishOut
from app.schemas.common import MessageResponse
from app.utils.auth import get_current_admin
from uuid import UUID
from typing import Optional
import openpyxl
import io

router = APIRouter(prefix="/admin", tags=["管理后台"])


# ==================== Canteens CRUD ====================

@router.post("/canteens", response_model=CanteenOut, status_code=201)
async def create_canteen(
    data: CanteenCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """新增食堂"""
    canteen = Canteen(**data.model_dump())
    db.add(canteen)
    await db.flush()
    return CanteenOut(
        id=canteen.id, name=canteen.name, location=canteen.location,
        latitude=canteen.latitude, longitude=canteen.longitude,
        opening_hours=canteen.opening_hours, image_url=canteen.image_url,
        description=canteen.description, window_count=0,
        created_at=canteen.created_at, updated_at=canteen.updated_at,
    )


@router.put("/canteens/{canteen_id}", response_model=CanteenOut)
async def update_canteen(
    canteen_id: UUID, data: CanteenUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """更新食堂"""
    q = select(Canteen).where(Canteen.id == canteen_id)
    result = await db.execute(q)
    canteen = result.scalar_one_or_none()
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")

    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(canteen, key, val)
    await db.flush()

    return CanteenOut(
        id=canteen.id, name=canteen.name, location=canteen.location,
        latitude=canteen.latitude, longitude=canteen.longitude,
        opening_hours=canteen.opening_hours, image_url=canteen.image_url,
        description=canteen.description, window_count=0,
        created_at=canteen.created_at, updated_at=canteen.updated_at,
    )


@router.delete("/canteens/{canteen_id}", response_model=MessageResponse)
async def delete_canteen(
    canteen_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """删除食堂"""
    q = select(Canteen).where(Canteen.id == canteen_id)
    result = await db.execute(q)
    canteen = result.scalar_one_or_none()
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")
    await db.delete(canteen)
    await db.flush()
    return MessageResponse(message="删除成功")


# ==================== Windows CRUD ====================

@router.post("/windows", response_model=WindowOut, status_code=201)
async def create_window(
    data: WindowCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """新增窗口"""
    # Verify canteen exists
    c_q = select(Canteen).where(Canteen.id == data.canteen_id)
    c_result = await db.execute(c_q)
    canteen = c_result.scalar_one_or_none()
    if not canteen:
        raise HTTPException(status_code=404, detail="食堂不存在")

    window = Window(**data.model_dump())
    db.add(window)
    await db.flush()

    return WindowOut(
        id=window.id, canteen_id=window.canteen_id, canteen_name=canteen.name,
        name=window.name, window_number=window.window_number,
        category=window.category, payment_methods=window.payment_methods,
        avg_rating=0, rating_count=0, is_active=window.is_active,
        image_url=window.image_url, description=window.description, dish_count=0,
        created_at=window.created_at, updated_at=window.updated_at,
    )


@router.put("/windows/{window_id}", response_model=WindowOut)
async def update_window(
    window_id: UUID, data: WindowUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """更新窗口"""
    q = select(Window).where(Window.id == window_id)
    result = await db.execute(q)
    window = result.scalar_one_or_none()
    if not window:
        raise HTTPException(status_code=404, detail="窗口不存在")

    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(window, key, val)
    await db.flush()

    c_q = select(Canteen.name).where(Canteen.id == window.canteen_id)
    c_r = await db.execute(c_q)
    cn = c_r.scalar_one()

    return WindowOut(
        id=window.id, canteen_id=window.canteen_id, canteen_name=cn,
        name=window.name, window_number=window.window_number,
        category=window.category, payment_methods=window.payment_methods,
        avg_rating=window.avg_rating, rating_count=window.rating_count,
        is_active=window.is_active, image_url=window.image_url,
        description=window.description, dish_count=0,
        created_at=window.created_at, updated_at=window.updated_at,
    )


@router.delete("/windows/{window_id}", response_model=MessageResponse)
async def delete_window(
    window_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """删除窗口"""
    q = select(Window).where(Window.id == window_id)
    result = await db.execute(q)
    window = result.scalar_one_or_none()
    if not window:
        raise HTTPException(status_code=404, detail="窗口不存在")
    await db.delete(window)
    await db.flush()
    return MessageResponse(message="删除成功")


# ==================== Dishes CRUD ====================

@router.post("/dishes", response_model=DishOut, status_code=201)
async def create_dish(
    data: DishCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """新增菜品"""
    w_q = select(Window).where(Window.id == data.window_id)
    w_result = await db.execute(w_q)
    window = w_result.scalar_one_or_none()
    if not window:
        raise HTTPException(status_code=404, detail="窗口不存在")

    dish = Dish(**data.model_dump())
    db.add(dish)
    await db.flush()

    c_q = select(Canteen.name).where(Canteen.id == window.canteen_id)
    c_r = await db.execute(c_q)
    cn = c_r.scalar_one()

    return DishOut(
        id=dish.id, window_id=dish.window_id, window_name=window.name,
        canteen_id=window.canteen_id, canteen_name=cn,
        name=dish.name, category=dish.category, price=float(dish.price),
        unit=dish.unit, image_url=dish.image_url, nutrition=dish.nutrition,
        is_available=dish.is_available, is_recommended=dish.is_recommended,
        avg_rating=0, rating_count=0,
        created_at=dish.created_at, updated_at=dish.updated_at,
    )


@router.put("/dishes/{dish_id}", response_model=DishOut)
async def update_dish(
    dish_id: UUID, data: DishUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """更新菜品"""
    q = select(Dish).where(Dish.id == dish_id)
    result = await db.execute(q)
    dish = result.scalar_one_or_none()
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")

    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(dish, key, val)
    await db.flush()

    w_q = select(Window.name, Window.id, Canteen.id, Canteen.name).join(Canteen).where(Window.id == dish.window_id)
    w_r = await db.execute(w_q)
    wn, wid, cid, cn = w_r.one()

    return DishOut(
        id=dish.id, window_id=wid, window_name=wn,
        canteen_id=cid, canteen_name=cn,
        name=dish.name, category=dish.category, price=float(dish.price),
        unit=dish.unit, image_url=dish.image_url, nutrition=dish.nutrition,
        is_available=dish.is_available, is_recommended=dish.is_recommended,
        avg_rating=dish.avg_rating, rating_count=dish.rating_count,
        created_at=dish.created_at, updated_at=dish.updated_at,
    )


@router.delete("/dishes/{dish_id}", response_model=MessageResponse)
async def delete_dish(
    dish_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """删除菜品"""
    q = select(Dish).where(Dish.id == dish_id)
    result = await db.execute(q)
    dish = result.scalar_one_or_none()
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    await db.delete(dish)
    await db.flush()
    return MessageResponse(message="删除成功")


@router.post("/dishes/batch", response_model=MessageResponse)
async def batch_import_dishes(
    window_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """批量导入菜品 (Excel)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传 Excel 文件 (.xlsx)")

    # Verify window
    w_q = select(Window).where(Window.id == window_id)
    w_result = await db.execute(w_q)
    if not w_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="窗口不存在")

    contents = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(contents))
    ws = wb.active

    count = 0
    # Expected columns: name, category, price, unit, is_available
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        name = str(row[0]).strip()
        category = str(row[1]).strip() if len(row) > 1 and row[1] else None
        price = float(row[2]) if len(row) > 2 and row[2] else 0.0
        unit = str(row[3]).strip() if len(row) > 3 and row[3] else "份"
        is_avail = bool(row[4]) if len(row) > 4 else True

        dish = Dish(
            window_id=window_id, name=name, category=category,
            price=price, unit=unit, is_available=is_avail,
        )
        db.add(dish)
        count += 1

    await db.flush()
    return MessageResponse(message=f"成功导入 {count} 个菜品")
