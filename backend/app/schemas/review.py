from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ReviewCreate(BaseModel):
    window_id: UUID
    dish_id: Optional[UUID] = None
    rating: int = Field(..., ge=1, le=5)
    content: Optional[str] = None
    images: Optional[list[str]] = None
    tags: Optional[list[str]] = None


class ReviewOut(BaseModel):
    id: UUID
    user_id: UUID
    user_nickname: str = ""
    user_avatar: Optional[str] = None
    dish_id: Optional[UUID] = None
    dish_name: Optional[str] = None
    window_id: UUID
    window_name: str = ""
    rating: int
    content: Optional[str]
    images: Optional[list]
    tags: Optional[list]
    like_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListOut(BaseModel):
    id: UUID
    user_id: UUID
    user_nickname: str = ""
    user_avatar: Optional[str] = None
    dish_id: Optional[UUID] = None
    dish_name: Optional[str] = None
    rating: int
    content: Optional[str]
    images: Optional[list]
    tags: Optional[list]
    like_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
