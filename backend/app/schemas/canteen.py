from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class CanteenCreate(BaseModel):
    name: str = Field(..., max_length=100)
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_hours: Optional[dict] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class CanteenUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_hours: Optional[dict] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class CanteenOut(BaseModel):
    id: UUID
    name: str
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    opening_hours: Optional[dict]
    image_url: Optional[str]
    description: Optional[str]
    window_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CanteenListOut(BaseModel):
    id: UUID
    name: str
    location: Optional[str]
    image_url: Optional[str]
    window_count: int = 0

    model_config = {"from_attributes": True}
