from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class DishCreate(BaseModel):
    window_id: UUID
    name: str = Field(..., max_length=100)
    category: Optional[str] = None
    price: float = Field(..., ge=0)
    unit: str = "份"
    image_url: Optional[str] = None
    nutrition: Optional[dict] = None
    is_available: bool = True
    is_recommended: bool = False


class DishUpdate(BaseModel):
    window_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[dict] = None
    is_available: Optional[bool] = None
    is_recommended: Optional[bool] = None


class NutritionOut(BaseModel):
    calories: Optional[float] = None  # kcal
    protein: Optional[float] = None  # g
    fat: Optional[float] = None  # g
    carbs: Optional[float] = None  # g
    fiber: Optional[float] = None  # g
    sodium: Optional[float] = None  # mg


class DishOut(BaseModel):
    id: UUID
    window_id: UUID
    window_name: str = ""
    canteen_id: Optional[UUID] = None
    canteen_name: str = ""
    name: str
    category: Optional[str]
    price: float
    unit: str
    image_url: Optional[str]
    nutrition: Optional[dict]
    is_available: bool
    is_recommended: bool
    avg_rating: float
    rating_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DishListOut(BaseModel):
    id: UUID
    window_id: UUID
    window_name: str = ""
    canteen_name: str = ""
    name: str
    category: Optional[str]
    price: float
    unit: str
    image_url: Optional[str]
    nutrition: Optional[dict]
    is_available: bool
    is_recommended: bool
    avg_rating: float
    rating_count: int

    model_config = {"from_attributes": True}


class CombinedNutritionRequest(BaseModel):
    dish_ids: list[UUID]
