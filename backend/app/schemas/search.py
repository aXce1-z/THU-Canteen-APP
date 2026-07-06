from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class SearchResult(BaseModel):
    dishes: list["SearchDishItem"] = []
    windows: list["SearchWindowItem"] = []
    canteens: list["SearchCanteenItem"] = []
    total_count: int = 0


class SearchDishItem(BaseModel):
    id: UUID
    name: str
    category: Optional[str]
    price: float
    unit: str
    image_url: Optional[str]
    window_id: UUID
    window_name: str
    canteen_id: Optional[UUID] = None
    canteen_name: str
    avg_rating: float
    is_available: bool


class SearchWindowItem(BaseModel):
    id: UUID
    name: str
    canteen_name: str
    category: Optional[str]
    avg_rating: float
    matching_dishes: list[str] = []


class SearchCanteenItem(BaseModel):
    id: UUID
    name: str
    location: Optional[str]
    image_url: Optional[str]
    window_count: int = 0


class SearchSuggestion(BaseModel):
    suggestions: list[str]
