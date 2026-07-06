from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.review import Review
from app.models.window import Window
from app.models.dish import Dish
from app.models.canteen import Canteen
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut, ReviewListOut
from app.schemas.common import PaginatedResponse
from uuid import UUID
import math

router = APIRouter(prefix="/reviews", tags=["评价"])


async def _update_window_rating(db: AsyncSession, window_id: UUID):
    """更新窗口平均评分"""
    avg_q = select(func.avg(Review.rating), func.count(Review.id)).where(
        Review.window_id == window_id,
        Review.is_approved == True,
    )
    result = await db.execute(avg_q)
    avg_rating, count = result.one()
    await db.execute(
        update(Window)
        .where(Window.id == window_id)
        .values(avg_rating=round(float(avg_rating or 0), 1), rating_count=count or 0)
    )


async def _update_dish_rating(db: AsyncSession, dish_id: UUID):
    """更新菜品平均评分"""
    avg_q = select(func.avg(Review.rating), func.count(Review.id)).where(
        Review.dish_id == dish_id,
        Review.is_approved == True,
    )
    result = await db.execute(avg_q)
    avg_rating, count = result.one()
    await db.execute(
        update(Dish)
        .where(Dish.id == dish_id)
        .values(avg_rating=round(float(avg_rating or 0), 1), rating_count=count or 0)
    )


@router.get("/windows/{window_id}", response_model=PaginatedResponse[ReviewListOut])
async def get_window_reviews(
    window_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("latest", pattern="^(latest|hot)$"),
    db: AsyncSession = Depends(get_db),
):
    """获取窗口评价列表"""
    conditions = [Review.window_id == window_id, Review.is_approved == True]
    count_q = select(func.count(Review.id)).where(*conditions)
    total = (await db.execute(count_q)).scalar()

    q = (select(Review, User.nickname, User.avatar_url, Dish.name, Window.name)
         .join(User)
         .join(Window)
         .outerjoin(Dish)
         .where(*conditions))

    if sort == "hot":
        q = q.order_by(Review.like_count.desc(), Review.created_at.desc())
    else:
        q = q.order_by(Review.created_at.desc())

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    rows = result.all()

    items = [
        ReviewListOut(
            id=r.id, user_id=r.user_id, user_nickname=un, user_avatar=ua,
            dish_id=r.dish_id, dish_name=dn,
            rating=r.rating, content=r.content, images=r.images, tags=r.tags,
            like_count=r.like_count, created_at=r.created_at,
        )
        for r, un, ua, dn, wn in rows
    ]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size))
    )


@router.get("/dishes/{dish_id}", response_model=PaginatedResponse[ReviewListOut])
async def get_dish_reviews(
    dish_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取菜品评价列表"""
    conditions = [Review.dish_id == dish_id, Review.is_approved == True]
    count_q = select(func.count(Review.id)).where(*conditions)
    total = (await db.execute(count_q)).scalar()

    q = (select(Review, User.nickname, User.avatar_url, Dish.name, Window.name)
         .join(User)
         .join(Window)
         .outerjoin(Dish)
         .where(*conditions)
         .order_by(Review.created_at.desc())
         .offset((page - 1) * page_size).limit(page_size))
    result = await db.execute(q)
    rows = result.all()

    items = [
        ReviewListOut(
            id=r.id, user_id=r.user_id, user_nickname=un, user_avatar=ua,
            dish_id=r.dish_id, dish_name=dn,
            rating=r.rating, content=r.content, images=r.images, tags=r.tags,
            like_count=r.like_count, created_at=r.created_at,
        )
        for r, un, ua, dn, wn in rows
    ]

    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size))
    )


@router.post("/windows/{window_id}", response_model=ReviewOut, status_code=201)
async def create_review(
    window_id: UUID,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    """发表评价"""
    # For MVP, use a mock user. In production, get from JWT token.
    # Check if a user exists, otherwise create a demo user
    user_q = select(User).limit(1)
    user_result = await db.execute(user_q)
    user = user_result.scalar_one_or_none()

    if not user:
        user = User(openid="demo_user", nickname="同学", role="user")
        db.add(user)
        await db.flush()

    # Verify window exists
    win_q = select(Window).where(Window.id == window_id)
    win_result = await db.execute(win_q)
    window = win_result.scalar_one_or_none()
    if not window:
        raise HTTPException(status_code=404, detail="窗口不存在")

    review = Review(
        user_id=user.id,
        window_id=window_id,
        dish_id=review_data.dish_id,
        rating=review_data.rating,
        content=review_data.content,
        images=review_data.images,
        tags=review_data.tags,
    )
    db.add(review)
    await db.flush()

    # Update ratings
    await _update_window_rating(db, window_id)
    if review_data.dish_id:
        await _update_dish_rating(db, review_data.dish_id)

    return ReviewOut(
        id=review.id, user_id=user.id, user_nickname=user.nickname,
        user_avatar=user.avatar_url, dish_id=review.dish_id, dish_name=None,
        window_id=review.window_id, window_name=window.name,
        rating=review.rating, content=review.content, images=review.images,
        tags=review.tags, like_count=0,
        created_at=review.created_at, updated_at=review.updated_at,
    )


@router.post("/{review_id}/like")
async def like_review(review_id: UUID, db: AsyncSession = Depends(get_db)):
    """点赞评价"""
    q = select(Review).where(Review.id == review_id)
    result = await db.execute(q)
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")

    review.like_count += 1
    await db.flush()
    return {"like_count": review.like_count, "success": True}
