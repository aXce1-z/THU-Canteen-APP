from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.dish import Dish
from app.schemas.dish import NutritionOut, CombinedNutritionRequest
from uuid import UUID

router = APIRouter(prefix="/nutrition", tags=["营养分析"])


@router.post("/analyze", response_model=NutritionOut)
async def analyze_combined_nutrition(
    data: CombinedNutritionRequest,
    db: AsyncSession = Depends(get_db),
):
    """组合餐营养分析 - 汇总多个菜品的营养成分"""
    if not data.dish_ids:
        raise HTTPException(status_code=400, detail="请选择至少一个菜品")

    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 0.0,
        "fiber": 0.0,
        "sodium": 0.0,
    }

    for dish_id in data.dish_ids:
        q = select(Dish.nutrition, Dish.name).where(Dish.id == dish_id)
        result = await db.execute(q)
        row = result.one_or_none()
        if not row:
            continue

        nutrition, name = row
        if nutrition:
            for key in totals:
                totals[key] += float(nutrition.get(key, 0) or 0)

    return NutritionOut(**totals)


# Pre-built common dish nutrition database
COMMON_NUTRITION = {
    "米饭": {"calories": 116, "protein": 2.6, "fat": 0.3, "carbs": 25.9, "fiber": 0.3, "sodium": 2},
    "馒头": {"calories": 223, "protein": 7.0, "fat": 1.1, "carbs": 44.2, "fiber": 1.3, "sodium": 165},
    "红烧肉": {"calories": 478, "protein": 8.0, "fat": 46.0, "carbs": 6.0, "fiber": 0, "sodium": 480},
    "番茄炒蛋": {"calories": 87, "protein": 4.6, "fat": 5.8, "carbs": 4.1, "fiber": 0.6, "sodium": 210},
    "宫保鸡丁": {"calories": 190, "protein": 18.0, "fat": 11.0, "carbs": 6.0, "fiber": 1.0, "sodium": 520},
    "麻婆豆腐": {"calories": 126, "protein": 8.0, "fat": 8.0, "carbs": 5.0, "fiber": 1.2, "sodium": 580},
    "鱼香肉丝": {"calories": 155, "protein": 12.0, "fat": 10.0, "carbs": 7.0, "fiber": 0.8, "sodium": 500},
    "回锅肉": {"calories": 298, "protein": 13.0, "fat": 26.0, "carbs": 4.0, "fiber": 0.5, "sodium": 460},
    "清炒时蔬": {"calories": 45, "protein": 2.0, "fat": 3.0, "carbs": 3.0, "fiber": 1.5, "sodium": 150},
    "水饺": {"calories": 240, "protein": 9.0, "fat": 8.0, "carbs": 33.0, "fiber": 1.0, "sodium": 350},
    "生煎包": {"calories": 270, "protein": 10.0, "fat": 13.0, "carbs": 29.0, "fiber": 0.8, "sodium": 400},
    "牛肉面": {"calories": 380, "protein": 15.0, "fat": 8.0, "carbs": 58.0, "fiber": 2.0, "sodium": 650},
    "炸鸡腿": {"calories": 310, "protein": 20.0, "fat": 22.0, "carbs": 8.0, "fiber": 0, "sodium": 380},
    "酸辣粉": {"calories": 180, "protein": 3.0, "fat": 5.0, "carbs": 30.0, "fiber": 1.5, "sodium": 700},
    "蛋炒饭": {"calories": 210, "protein": 6.0, "fat": 8.0, "carbs": 28.0, "fiber": 0.5, "sodium": 300},
    "紫菜蛋花汤": {"calories": 30, "protein": 2.0, "fat": 1.0, "carbs": 3.0, "fiber": 0.3, "sodium": 350},
    "豆浆": {"calories": 31, "protein": 3.0, "fat": 1.5, "carbs": 1.5, "fiber": 0, "sodium": 2},
    "油条": {"calories": 386, "protein": 6.9, "fat": 17.6, "carbs": 51.0, "fiber": 0.9, "sodium": 585},
}


@router.get("/common-db")
async def get_common_nutrition_db():
    """获取预置的常见菜品营养成分数据库"""
    return COMMON_NUTRITION


@router.get("/match/{dish_name}")
async def match_nutrition(dish_name: str):
    """根据菜品名称模糊匹配营养成分（用于新建菜品时自动填充）"""
    from difflib import get_close_matches
    matches = get_close_matches(dish_name, COMMON_NUTRITION.keys(), n=3, cutoff=0.3)
    results = {}
    for m in matches:
        results[m] = COMMON_NUTRITION[m]
    return {"dish_name": dish_name, "matches": results}
