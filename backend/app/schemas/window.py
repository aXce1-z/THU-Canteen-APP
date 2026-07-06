from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class WindowCreate(BaseModel):
    canteen_id: UUID
    name: str = Field(..., max_length=100)
    window_number: Optional[str] = None
    category: Optional[str] = None
    payment_methods: list[str] = ["campus_card"]
    is_active: bool = True
    image_url: Optional[str] = None
    description: Optional[str] = None


class WindowUpdate(BaseModel):
    canteen_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=100)
    window_number: Optional[str] = None
    category: Optional[str] = None
    payment_methods: Optional[list[str]] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class WindowOut(BaseModel):
    id: UUID
    canteen_id: UUID
    canteen_name: str = ""
    name: str
    window_number: Optional[str]
    category: Optional[str]
    payment_methods: Optional[list]
    avg_rating: float
    rating_count: int
    is_active: bool
    image_url: Optional[str]
    description: Optional[str]
    dish_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WindowListOut(BaseModel):
    id: UUID
    canteen_id: UUID
    canteen_name: str = ""
    name: str
    window_number: Optional[str]
    category: Optional[str]
    payment_methods: Optional[list]
    avg_rating: float
    rating_count: int
    is_active: bool
    image_url: Optional[str]
    dish_count: int = 0

    model_config = {"from_attributes": True}
