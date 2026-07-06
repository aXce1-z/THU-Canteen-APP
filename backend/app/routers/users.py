from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, WeChatLoginRequest, TokenResponse
from app.config import get_settings
from jose import jwt
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter(prefix="/users", tags=["用户"])

settings = get_settings()


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/login/wechat", response_model=TokenResponse)
async def wechat_login(data: WeChatLoginRequest, db: AsyncSession = Depends(get_db)):
    """微信登录"""
    # In production: call WeChat API to exchange code for openid
    # For MVP/demo: accept code as a mock identifier
    openid = f"wechat_{data.code}"

    # Find or create user
    q = select(User).where(User.openid == openid)
    result = await db.execute(q)
    user = result.scalar_one_or_none()

    if not user:
        user = User(openid=openid, nickname="清华同学")
        db.add(user)
        await db.flush()

    token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id, openid=user.openid, nickname=user.nickname,
            avatar_url=user.avatar_url, role=user.role.value,
            contribution_points=user.contribution_points,
        ),
    )


@router.get("/me", response_model=UserOut)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户信息（MVP: 返回第一个用户）"""
    q = select(User).limit(1)
    result = await db.execute(q)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserOut(
        id=user.id, openid=user.openid, nickname=user.nickname,
        avatar_url=user.avatar_url, role=user.role.value,
        contribution_points=user.contribution_points,
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取用户信息"""
    q = select(User).where(User.id == user_id)
    result = await db.execute(q)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserOut(
        id=user.id, openid=user.openid, nickname=user.nickname,
        avatar_url=user.avatar_url, role=user.role.value,
        contribution_points=user.contribution_points,
    )
