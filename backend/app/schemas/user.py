from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    openid: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    openid: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    role: str
    contribution_points: int

    model_config = {"from_attributes": True}


class WeChatLoginRequest(BaseModel):
    code: str = Field(..., description="微信登录 code")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"
