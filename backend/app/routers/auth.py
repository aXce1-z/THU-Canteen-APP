"""认证路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, TokenResponse
from app.utils.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """管理后台登录（用户名+密码）"""
    q = select(User).where(User.openid == data.username)
    result = await db.execute(q)
    user = result.scalar_one_or_none()

    if user is None:
        # Check if there's a mock admin user from seed data
        q2 = select(User).where(User.openid == data.username.split("@")[0] if "@" not in data.username else data.username)
        result2 = await db.execute(q2)
        user = result2.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # For seed data users, accept "admin123" as default password
    # In production, use verify_password(data.password, user.hashed_password)
    valid = False
    if hasattr(user, 'hashed_password') and user.hashed_password:
        valid = verify_password(data.password, user.hashed_password)
    else:
        # MVP: accept default password for seed users
        valid = (data.password == "admin123")

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token(user.id, user.role.value)
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id, openid=user.openid, nickname=user.nickname,
            avatar_url=user.avatar_url, role=user.role.value,
            contribution_points=user.contribution_points,
        ),
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserOut(
        id=user.id, openid=user.openid, nickname=user.nickname,
        avatar_url=user.avatar_url, role=user.role.value,
        contribution_points=user.contribution_points,
    )
