from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.models.dish import Dish
from app.models.window import Window
from app.models.canteen import Canteen
from app.schemas.search import SearchResult, SearchDishItem, SearchWindowItem, SearchCanteenItem, SearchSuggestion
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("", response_model=SearchResult)
async def search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    canteen_id: Optional[UUID] = None,
    category: Optional[str] = None,
    sort: str = Query("relevance", pattern="^(relevance|rating|price_asc|price_desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """全文搜索菜品、窗口、食堂"""
    search_term = f"%{q}%"

    # 尝试 FTS5 搜索
    fts_ids = None
    try:
        from app.services.search_engine import search as fts_search
        fts_ids = fts_search(q, str(canteen_id) if canteen_id else None, category, limit=page_size * 2)
    except Exception:
        pass

    # --- Search dishes ---
    dish_conditions = []
    if fts_ids:
        # 优先使用 FTS 结果
        from sqlalchemy import cast, String
        dish_conditions.append(Dish.id.in_([UUID(x) for x in fts_ids]))
    else:
        # 回退到 ILIKE
        dish_conditions.append(
            or_(Dish.name.ilike(search_term), Dish.category.ilike(search_term))
        )
    if canteen_id:
        dish_conditions.append(Window.canteen_id == canteen_id)
    if category:
        dish_conditions.append(Dish.category == category)

    dish_q = (select(Dish, Window.name, Canteen.id, Canteen.name)
              .select_from(Dish)
              .join(Window).join(Canteen)
              .where(*dish_conditions))

    # Sort
    if sort == "rating":
        dish_q = dish_q.order_by(Dish.avg_rating.desc().nullslast())
    elif sort == "price_asc":
        dish_q = dish_q.order_by(Dish.price.asc())
    elif sort == "price_desc":
        dish_q = dish_q.order_by(Dish.price.desc())
    else:
        # relevance: exact match first, then partial
        dish_q = dish_q.order_by(
            Dish.name.ilike(f"{q}%").desc(),
            Dish.avg_rating.desc().nullslast(),
        )

    dish_q = dish_q.offset((page - 1) * page_size).limit(page_size)
    dish_result = await db.execute(dish_q)
    dish_rows = dish_result.all()

    dishes = [
        SearchDishItem(
            id=d.id, name=d.name, category=d.category,
            price=float(d.price), unit=d.unit, image_url=d.image_url,
            window_id=d.window_id, window_name=wn,
            canteen_id=cid, canteen_name=cn,
            avg_rating=d.avg_rating, is_available=d.is_available,
        )
        for d, wn, cid, cn in dish_rows
    ]

    # --- Search windows ---
    win_q = (select(Window, Canteen.name)
             .join(Canteen)
             .where(Window.name.ilike(search_term)))
    if canteen_id:
        win_q = win_q.where(Window.canteen_id == canteen_id)
    win_q = win_q.order_by(Window.avg_rating.desc().nullslast()).limit(10)
    win_result = await db.execute(win_q)
    win_rows = win_result.all()

    windows = [
        SearchWindowItem(
            id=w.id, name=w.name, canteen_name=cn,
            category=w.category, avg_rating=w.avg_rating,
        )
        for w, cn in win_rows
    ]

    # --- Search canteens ---
    can_q = select(Canteen).where(Canteen.name.ilike(search_term)).limit(5)
    can_result = await db.execute(can_q)
    canteens_rows = can_result.scalars().all()

    canteens = []
    for c in canteens_rows:
        wc = (await db.execute(select(func.count(Window.id)).where(Window.canteen_id == c.id))).scalar()
        canteens.append(SearchCanteenItem(
            id=c.id, name=c.name, location=c.location,
            image_url=c.image_url, window_count=wc or 0,
        ))

    total = len(dishes) + len(windows) + len(canteens)

    return SearchResult(
        dishes=dishes, windows=windows, canteens=canteens, total_count=total
    )


@router.get("/suggestions", response_model=SearchSuggestion)
async def search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """搜索自动补全（优先 FTS，回退 ILIKE）"""
    try:
        from app.services.search_engine import get_suggestions as fts_suggest
        fts_results = fts_suggest(q, limit)
        if fts_results:
            return SearchSuggestion(suggestions=fts_results)
    except Exception:
        pass

    # Fallback to ILIKE
    search_term = f"{q}%"
    dish_q = (select(Dish.name).where(Dish.name.ilike(search_term)).distinct().limit(limit))
    dish_result = await db.execute(dish_q)
    dish_names = dish_result.scalars().all()

    win_q = (select(Window.name).where(Window.name.ilike(search_term)).distinct().limit(limit))
    win_result = await db.execute(win_q)
    win_names = win_result.scalars().all()

    suggestions = list(dict.fromkeys(list(dish_names) + list(win_names)))[:limit]
    return SearchSuggestion(suggestions=suggestions)
