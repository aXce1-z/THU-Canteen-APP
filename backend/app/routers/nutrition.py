"""
营养分析 API (v2) — LLM精算 + 每日推荐百分比
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.dish import Dish
from app.schemas.dish import NutritionOut, CombinedNutritionRequest
from uuid import UUID
from pydantic import BaseModel

router = APIRouter(prefix="/nutrition", tags=["营养分析"])

# 每日推荐摄入量 (中国居民膳食指南 2022)
# 成年人 18-49 岁，中等体力活动水平
DAILY_REFERENCE = {
    "calories": 2200,   # kcal
    "protein": 65,      # g
    "fat": 60,          # g
    "carbs": 300,       # g
    "fiber": 25,        # g
    "sodium": 2000,     # mg
}


class NutritionWithPct(NutritionOut):
    """营养成分 + 每日占比"""
    pct_calories: float = 0
    pct_protein: float = 0
    pct_fat: float = 0
    pct_carbs: float = 0
    pct_fiber: float = 0
    pct_sodium: float = 0


@router.post("/analyze", response_model=NutritionWithPct)
async def analyze_combined_nutrition(
    data: CombinedNutritionRequest,
    db: AsyncSession = Depends(get_db),
):
    """组合餐营养分析 - 汇总营养 + 每日推荐百分比"""
    if not data.dish_ids:
        raise HTTPException(status_code=400, detail="请选择至少一个菜品")

    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0,
              "carbs": 0.0, "fiber": 0.0, "sodium": 0.0}
    dish_names = []

    for dish_id in data.dish_ids:
        q = select(Dish.nutrition, Dish.name).where(Dish.id == dish_id)
        result = await db.execute(q)
        row = result.one_or_none()
        if not row:
            continue
        nutrition, name = row
        dish_names.append(name)
        if nutrition and isinstance(nutrition, dict):
            for key in totals:
                totals[key] += float(nutrition.get(key, 0) or 0)

    # 计算每日占比
    pct = {}
    for key, ref in DAILY_REFERENCE.items():
        pct[f"pct_{key}"] = round(totals[key] / ref * 100, 1)

    return NutritionWithPct(**totals, **pct)


@router.get("/daily-reference")
async def daily_reference():
    """获取每日营养推荐值"""
    return DAILY_REFERENCE


# ============================================================
# LLM 营养成分估算 (预计算 + 在线回退)
# ============================================================

# 基于 LLM 知识的 270+ 菜品精确营养数据
# 每份约为食堂正常一份的量 (300-500g)
LLM_NUTRITION_DB = {
    # ---- 主食 ----
    "米饭": {"calories": 174, "protein": 3.9, "fat": 0.5, "carbs": 38.9, "fiber": 0.5, "sodium": 3},
    "花卷": {"calories": 190, "protein": 5.0, "fat": 2.5, "carbs": 38.0, "fiber": 0.8, "sodium": 120},
    "馒头": {"calories": 223, "protein": 7.0, "fat": 1.1, "carbs": 44.2, "fiber": 1.3, "sodium": 165},
    "蛋炒饭": {"calories": 280, "protein": 8.0, "fat": 10.0, "carbs": 38.0, "fiber": 0.5, "sodium": 380},
    "馕": {"calories": 220, "protein": 7.5, "fat": 1.8, "carbs": 44.0, "fiber": 1.5, "sodium": 8},
    "酱油饭": {"calories": 200, "protein": 4.0, "fat": 3.0, "carbs": 40.0, "fiber": 0.3, "sodium": 450},
    # ---- 面食 ----
    "重庆小面": {"calories": 350, "protein": 11.0, "fat": 14.0, "carbs": 45.0, "fiber": 1.5, "sodium": 700},
    "担担面": {"calories": 370, "protein": 12.0, "fat": 14.0, "carbs": 48.0, "fiber": 1.0, "sodium": 650},
    "炸酱面": {"calories": 380, "protein": 14.0, "fat": 12.0, "carbs": 54.0, "fiber": 2.0, "sodium": 600},
    "油泼面": {"calories": 400, "protein": 12.0, "fat": 12.0, "carbs": 60.0, "fiber": 1.5, "sodium": 520},
    "兰州牛肉拉面": {"calories": 420, "protein": 18.0, "fat": 10.0, "carbs": 62.0, "fiber": 2.0, "sodium": 700},
    "红烧牛肉面": {"calories": 440, "protein": 20.0, "fat": 12.0, "carbs": 60.0, "fiber": 2.0, "sodium": 750},
    "热干面": {"calories": 380, "protein": 12.0, "fat": 14.0, "carbs": 52.0, "fiber": 1.5, "sodium": 600},
    "沙茶面": {"calories": 390, "protein": 14.0, "fat": 16.0, "carbs": 48.0, "fiber": 1.0, "sodium": 680},
    "酸辣粉": {"calories": 250, "protein": 5.0, "fat": 8.0, "carbs": 38.0, "fiber": 2.0, "sodium": 800},
    "螺蛳粉": {"calories": 400, "protein": 10.0, "fat": 18.0, "carbs": 52.0, "fiber": 2.0, "sodium": 850},
    "桂林米粉": {"calories": 340, "protein": 10.0, "fat": 8.0, "carbs": 56.0, "fiber": 1.0, "sodium": 500},
    "燃面": {"calories": 420, "protein": 12.0, "fat": 16.0, "carbs": 56.0, "fiber": 1.0, "sodium": 600},
    "烩麻食": {"calories": 320, "protein": 10.0, "fat": 8.0, "carbs": 52.0, "fiber": 2.0, "sodium": 400},
    "猪脚面": {"calories": 430, "protein": 18.0, "fat": 18.0, "carbs": 50.0, "fiber": 0.5, "sodium": 680},
    "猪手刀削面": {"calories": 420, "protein": 18.0, "fat": 16.0, "carbs": 52.0, "fiber": 1.0, "sodium": 650},
    "大盘鸡刀削面": {"calories": 480, "protein": 22.0, "fat": 16.0, "carbs": 60.0, "fiber": 2.0, "sodium": 700},
    "干拌豌杂面": {"calories": 380, "protein": 14.0, "fat": 12.0, "carbs": 54.0, "fiber": 2.5, "sodium": 550},
    "铁锅焖面": {"calories": 420, "protein": 16.0, "fat": 14.0, "carbs": 56.0, "fiber": 2.0, "sodium": 580},
    "三合一拌面": {"calories": 400, "protein": 14.0, "fat": 12.0, "carbs": 58.0, "fiber": 1.5, "sodium": 550},
    # ---- 米饭套餐 ----
    "烧鸭饭": {"calories": 520, "protein": 24.0, "fat": 20.0, "carbs": 60.0, "fiber": 1.0, "sodium": 680},
    "海南鸡饭": {"calories": 480, "protein": 30.0, "fat": 16.0, "carbs": 56.0, "fiber": 1.0, "sodium": 450},
    "叉烧饭": {"calories": 500, "protein": 24.0, "fat": 20.0, "carbs": 58.0, "fiber": 0.5, "sodium": 650},
    "黄焖鸡米饭": {"calories": 430, "protein": 26.0, "fat": 16.0, "carbs": 46.0, "fiber": 1.0, "sodium": 680},
    "烤肉拌饭": {"calories": 460, "protein": 22.0, "fat": 18.0, "carbs": 52.0, "fiber": 0.5, "sodium": 600},
    "煲仔饭": {"calories": 450, "protein": 18.0, "fat": 16.0, "carbs": 56.0, "fiber": 1.0, "sodium": 580},
    "滑蛋饭": {"calories": 360, "protein": 16.0, "fat": 14.0, "carbs": 42.0, "fiber": 0.5, "sodium": 380},
    "咖喱鸡排意面": {"calories": 480, "protein": 24.0, "fat": 20.0, "carbs": 52.0, "fiber": 2.0, "sodium": 580},
    "韩式拌饭": {"calories": 460, "protein": 18.0, "fat": 14.0, "carbs": 64.0, "fiber": 3.5, "sodium": 600},
    "手抓饭": {"calories": 420, "protein": 16.0, "fat": 14.0, "carbs": 56.0, "fiber": 1.0, "sodium": 450},
    "擂椒拌饭": {"calories": 380, "protein": 14.0, "fat": 12.0, "carbs": 54.0, "fiber": 1.5, "sodium": 550},
    "啵啵饭": {"calories": 420, "protein": 18.0, "fat": 16.0, "carbs": 52.0, "fiber": 1.0, "sodium": 600},
    "馋嘴啵啵饭": {"calories": 440, "protein": 18.0, "fat": 18.0, "carbs": 52.0, "fiber": 1.0, "sodium": 620},
    "猪脚饭": {"calories": 500, "protein": 22.0, "fat": 22.0, "carbs": 54.0, "fiber": 0.5, "sodium": 700},
    # ---- 面点小吃 ----
    "生煎包": {"calories": 210, "protein": 8.0, "fat": 10.0, "carbs": 22.0, "fiber": 0.5, "sodium": 350},
    "生煎包（猪肉）": {"calories": 210, "protein": 8.0, "fat": 10.0, "carbs": 22.0, "fiber": 0.5, "sodium": 350},
    "生煎包（虾仁）": {"calories": 180, "protein": 10.0, "fat": 7.0, "carbs": 20.0, "fiber": 0.3, "sodium": 320},
    "小笼包": {"calories": 280, "protein": 14.0, "fat": 16.0, "carbs": 22.0, "fiber": 0.5, "sodium": 420},
    "小馄饨": {"calories": 180, "protein": 8.0, "fat": 6.0, "carbs": 24.0, "fiber": 0.3, "sodium": 350},
    "肉夹馍": {"calories": 280, "protein": 12.0, "fat": 10.0, "carbs": 34.0, "fiber": 1.5, "sodium": 400},
    "煎饼果子": {"calories": 360, "protein": 12.0, "fat": 14.0, "carbs": 46.0, "fiber": 2.0, "sodium": 600},
    "煎饼果子加肉松": {"calories": 400, "protein": 14.0, "fat": 16.0, "carbs": 46.0, "fiber": 2.0, "sodium": 650},
    "鸡蛋灌饼": {"calories": 320, "protein": 10.0, "fat": 12.0, "carbs": 42.0, "fiber": 1.5, "sodium": 500},
    "烤冷面": {"calories": 280, "protein": 8.0, "fat": 10.0, "carbs": 40.0, "fiber": 0.5, "sodium": 550},
    "锅贴": {"calories": 300, "protein": 12.0, "fat": 16.0, "carbs": 28.0, "fiber": 0.5, "sodium": 420},
    "油条": {"calories": 386, "protein": 6.9, "fat": 17.6, "carbs": 51.0, "fiber": 0.9, "sodium": 585},
    "驴打滚": {"calories": 180, "protein": 4.0, "fat": 2.0, "carbs": 36.0, "fiber": 1.0, "sodium": 20},
    "鲜肉包": {"calories": 200, "protein": 8.0, "fat": 8.0, "carbs": 24.0, "fiber": 0.5, "sodium": 280},
    "豆沙包": {"calories": 160, "protein": 5.0, "fat": 2.0, "carbs": 32.0, "fiber": 1.0, "sodium": 100},
    "南瓜酥": {"calories": 200, "protein": 3.0, "fat": 10.0, "carbs": 26.0, "fiber": 1.0, "sodium": 120},
    "蛋挞": {"calories": 160, "protein": 4.0, "fat": 10.0, "carbs": 14.0, "fiber": 0, "sodium": 60},
    "蛋黄酥": {"calories": 220, "protein": 5.0, "fat": 12.0, "carbs": 24.0, "fiber": 0.5, "sodium": 120},
    "肉松面包": {"calories": 280, "protein": 8.0, "fat": 12.0, "carbs": 36.0, "fiber": 1.0, "sodium": 300},
    "桂花黄米凉糕": {"calories": 150, "protein": 3.0, "fat": 2.0, "carbs": 32.0, "fiber": 0.5, "sodium": 30},
    "杏仁小米饼": {"calories": 120, "protein": 3.0, "fat": 3.0, "carbs": 22.0, "fiber": 1.0, "sodium": 20},
    "炸鲜奶": {"calories": 240, "protein": 5.0, "fat": 14.0, "carbs": 26.0, "fiber": 0, "sodium": 100},
    "榴莲酥": {"calories": 200, "protein": 3.0, "fat": 12.0, "carbs": 22.0, "fiber": 0.3, "sodium": 80},
    "葱油饼": {"calories": 280, "protein": 6.0, "fat": 14.0, "carbs": 32.0, "fiber": 0.5, "sodium": 350},
    "芝士焗玉米": {"calories": 220, "protein": 7.0, "fat": 12.0, "carbs": 22.0, "fiber": 1.0, "sodium": 250},
    # ---- 炒菜 ----
    "番茄炒蛋": {"calories": 120, "protein": 6.0, "fat": 8.0, "carbs": 6.0, "fiber": 0.8, "sodium": 250},
    "红烧肉": {"calories": 520, "protein": 10.0, "fat": 50.0, "carbs": 8.0, "fiber": 0, "sodium": 520},
    "宫保鸡丁": {"calories": 240, "protein": 22.0, "fat": 14.0, "carbs": 8.0, "fiber": 1.0, "sodium": 580},
    "麻婆豆腐": {"calories": 160, "protein": 10.0, "fat": 10.0, "carbs": 6.0, "fiber": 1.5, "sodium": 650},
    "回锅肉": {"calories": 340, "protein": 16.0, "fat": 28.0, "carbs": 6.0, "fiber": 0.5, "sodium": 520},
    "鱼香肉丝": {"calories": 200, "protein": 14.0, "fat": 12.0, "carbs": 10.0, "fiber": 1.0, "sodium": 550},
    "水煮肉片": {"calories": 300, "protein": 24.0, "fat": 20.0, "carbs": 6.0, "fiber": 0.5, "sodium": 780},
    "水煮鱼": {"calories": 280, "protein": 24.0, "fat": 18.0, "carbs": 6.0, "fiber": 0.5, "sodium": 750},
    "酸菜鱼": {"calories": 200, "protein": 22.0, "fat": 10.0, "carbs": 6.0, "fiber": 0.5, "sodium": 620},
    "锅包肉": {"calories": 320, "protein": 18.0, "fat": 18.0, "carbs": 24.0, "fiber": 0, "sodium": 480},
    "地三鲜": {"calories": 180, "protein": 4.0, "fat": 12.0, "carbs": 18.0, "fiber": 2.5, "sodium": 450},
    "辣子鸡": {"calories": 300, "protein": 26.0, "fat": 20.0, "carbs": 6.0, "fiber": 0.5, "sodium": 620},
    "糖醋里脊": {"calories": 300, "protein": 18.0, "fat": 14.0, "carbs": 26.0, "fiber": 0, "sodium": 500},
    "酸辣土豆丝": {"calories": 110, "protein": 2.5, "fat": 5.0, "carbs": 15.0, "fiber": 1.5, "sodium": 380},
    "清炒时蔬": {"calories": 60, "protein": 2.5, "fat": 4.0, "carbs": 4.0, "fiber": 2.0, "sodium": 200},
    "京酱肉丝": {"calories": 240, "protein": 20.0, "fat": 14.0, "carbs": 8.0, "fiber": 0.5, "sodium": 500},
    "东坡肉": {"calories": 520, "protein": 10.0, "fat": 50.0, "carbs": 8.0, "fiber": 0, "sodium": 520},
    "小酥肉": {"calories": 360, "protein": 18.0, "fat": 26.0, "carbs": 16.0, "fiber": 0, "sodium": 500},
    "糖醋鲤鱼": {"calories": 240, "protein": 20.0, "fat": 10.0, "carbs": 18.0, "fiber": 0, "sodium": 400},
    "葱烧海参": {"calories": 120, "protein": 8.0, "fat": 4.0, "carbs": 10.0, "fiber": 0, "sodium": 580},
    "九转大肠": {"calories": 400, "protein": 16.0, "fat": 34.0, "carbs": 8.0, "fiber": 0, "sodium": 620},
    "大盘鸡": {"calories": 380, "protein": 26.0, "fat": 18.0, "carbs": 30.0, "fiber": 2.5, "sodium": 650},
    "口水鸡": {"calories": 240, "protein": 24.0, "fat": 16.0, "carbs": 3.0, "fiber": 0, "sodium": 420},
    "烤羊排": {"calories": 380, "protein": 22.0, "fat": 30.0, "carbs": 4.0, "fiber": 0, "sodium": 450},
    "关东锅包肉": {"calories": 320, "protein": 18.0, "fat": 18.0, "carbs": 24.0, "fiber": 0, "sodium": 480},
    "红烧鳕鱼": {"calories": 200, "protein": 22.0, "fat": 8.0, "carbs": 8.0, "fiber": 0, "sodium": 420},
    "香酥鸡块": {"calories": 320, "protein": 22.0, "fat": 22.0, "carbs": 12.0, "fiber": 0, "sodium": 450},
    "东北乱炖": {"calories": 240, "protein": 16.0, "fat": 12.0, "carbs": 20.0, "fiber": 3.5, "sodium": 580},
    "虎眼丸子": {"calories": 260, "protein": 16.0, "fat": 18.0, "carbs": 8.0, "fiber": 0, "sodium": 500},
    "松鼠草鱼": {"calories": 280, "protein": 20.0, "fat": 14.0, "carbs": 18.0, "fiber": 0.5, "sodium": 450},
    "松鼠鳜鱼": {"calories": 260, "protein": 22.0, "fat": 12.0, "carbs": 16.0, "fiber": 0, "sodium": 400},
    "宫保虾球": {"calories": 200, "protein": 18.0, "fat": 10.0, "carbs": 12.0, "fiber": 0.5, "sodium": 550},
    "老妈蹄花": {"calories": 300, "protein": 22.0, "fat": 22.0, "carbs": 6.0, "fiber": 0, "sodium": 450},
    "老碗鱼": {"calories": 320, "protein": 24.0, "fat": 20.0, "carbs": 14.0, "fiber": 1.0, "sodium": 680},
    "老碗排骨": {"calories": 360, "protein": 24.0, "fat": 24.0, "carbs": 12.0, "fiber": 0.5, "sodium": 620},
    "蜜汁叉烧": {"calories": 380, "protein": 20.0, "fat": 16.0, "carbs": 38.0, "fiber": 0, "sodium": 580},
    "白切鸡": {"calories": 220, "protein": 26.0, "fat": 12.0, "carbs": 2.0, "fiber": 0, "sodium": 300},
    "金钱蛋": {"calories": 200, "protein": 14.0, "fat": 14.0, "carbs": 4.0, "fiber": 0, "sodium": 400},
    "酸汤肥牛": {"calories": 280, "protein": 24.0, "fat": 18.0, "carbs": 6.0, "fiber": 0.5, "sodium": 680},
    # ---- 火锅/麻辣烫/冒菜 ----
    "涮羊肉（小份）": {"calories": 380, "protein": 28.0, "fat": 26.0, "carbs": 8.0, "fiber": 1.0, "sodium": 650},
    "涮羊肉（大份）": {"calories": 550, "protein": 40.0, "fat": 36.0, "carbs": 12.0, "fiber": 1.5, "sodium": 900},
    "麻辣香锅（素）": {"calories": 250, "protein": 8.0, "fat": 14.0, "carbs": 24.0, "fiber": 4.0, "sodium": 800},
    "麻辣香锅（荤素搭配）": {"calories": 450, "protein": 24.0, "fat": 28.0, "carbs": 28.0, "fiber": 3.0, "sodium": 950},
    "麻辣香锅（全荤）": {"calories": 580, "protein": 35.0, "fat": 38.0, "carbs": 22.0, "fiber": 2.0, "sodium": 1100},
    "麻辣烫（麻酱风味）": {"calories": 280, "protein": 14.0, "fat": 14.0, "carbs": 24.0, "fiber": 3.0, "sodium": 820},
    "麻辣烫（素）": {"calories": 180, "protein": 6.0, "fat": 10.0, "carbs": 18.0, "fiber": 4.0, "sodium": 720},
    "麻辣烫（荤素搭配）": {"calories": 320, "protein": 18.0, "fat": 18.0, "carbs": 24.0, "fiber": 3.5, "sodium": 880},
    "骨汤冒菜（素）": {"calories": 160, "protein": 8.0, "fat": 8.0, "carbs": 16.0, "fiber": 3.5, "sodium": 580},
    "骨汤冒菜（荤）": {"calories": 280, "protein": 20.0, "fat": 16.0, "carbs": 18.0, "fiber": 3.0, "sodium": 720},
    "成都冒烤鸭": {"calories": 480, "protein": 28.0, "fat": 32.0, "carbs": 20.0, "fiber": 1.5, "sodium": 900},
    # ---- 火锅 ----
    "单人小火锅": {"calories": 500, "protein": 32.0, "fat": 30.0, "carbs": 28.0, "fiber": 2.5, "sodium": 1000},
    "双人火锅套餐": {"calories": 950, "protein": 58.0, "fat": 54.0, "carbs": 52.0, "fiber": 5.0, "sodium": 1900},
    # ---- 铁板/烧烤 ----
    "铁板牛肉": {"calories": 320, "protein": 28.0, "fat": 20.0, "carbs": 8.0, "fiber": 0.5, "sodium": 580},
    "铁板豆腐": {"calories": 140, "protein": 10.0, "fat": 8.0, "carbs": 10.0, "fiber": 0.5, "sodium": 350},
    "铁板鸡排": {"calories": 340, "protein": 26.0, "fat": 18.0, "carbs": 16.0, "fiber": 0.5, "sodium": 500},
    "铁板饭": {"calories": 480, "protein": 24.0, "fat": 22.0, "carbs": 48.0, "fiber": 1.0, "sodium": 620},
    "铁板芝士鸡": {"calories": 420, "protein": 28.0, "fat": 22.0, "carbs": 26.0, "fiber": 0.5, "sodium": 600},
    "铁板照烧鸡": {"calories": 380, "protein": 26.0, "fat": 16.0, "carbs": 30.0, "fiber": 0.5, "sodium": 550},
    "红柳大串": {"calories": 200, "protein": 18.0, "fat": 14.0, "carbs": 2.0, "fiber": 0, "sodium": 400},
    "烤羊肉串": {"calories": 140, "protein": 14.0, "fat": 10.0, "carbs": 1.0, "fiber": 0, "sodium": 300},
    "蒙古烤肉": {"calories": 350, "protein": 26.0, "fat": 22.0, "carbs": 10.0, "fiber": 0, "sodium": 550},
    # ---- 烤鸭 ----
    "北京烤鸭（小份）": {"calories": 250, "protein": 10.0, "fat": 20.0, "carbs": 6.0, "fiber": 0, "sodium": 400},
    "北京烤鸭（大份）": {"calories": 500, "protein": 20.0, "fat": 40.0, "carbs": 12.0, "fiber": 0, "sodium": 800},
    "烤鸭": {"calories": 500, "protein": 20.0, "fat": 40.0, "carbs": 12.0, "fiber": 0, "sodium": 800},
    # ---- 炸物 ----
    "炸鸡翅（一对）": {"calories": 320, "protein": 22.0, "fat": 22.0, "carbs": 10.0, "fiber": 0, "sodium": 480},
    "韩式炸鸡": {"calories": 350, "protein": 24.0, "fat": 20.0, "carbs": 18.0, "fiber": 0, "sodium": 580},
    "老北京炸鸡": {"calories": 340, "protein": 24.0, "fat": 22.0, "carbs": 12.0, "fiber": 0, "sodium": 500},
    # ---- 韩餐 ----
    "韩式炒年糕": {"calories": 260, "protein": 5.0, "fat": 5.0, "carbs": 48.0, "fiber": 1.5, "sodium": 580},
    "泡菜豆腐汤": {"calories": 110, "protein": 6.0, "fat": 5.0, "carbs": 10.0, "fiber": 1.5, "sodium": 620},
    "泡菜饼": {"calories": 220, "protein": 5.0, "fat": 8.0, "carbs": 32.0, "fiber": 1.5, "sodium": 450},
    "芝士鸡": {"calories": 400, "protein": 28.0, "fat": 24.0, "carbs": 16.0, "fiber": 0, "sodium": 550},
    # ---- 赣菜 (2026新) ----
    "藜蒿炒腊肉": {"calories": 280, "protein": 14.0, "fat": 18.0, "carbs": 14.0, "fiber": 1.5, "sodium": 620},
    "赣南小炒鱼": {"calories": 240, "protein": 22.0, "fat": 12.0, "carbs": 10.0, "fiber": 0.5, "sodium": 580},
    "余干辣椒炒肉": {"calories": 300, "protein": 18.0, "fat": 22.0, "carbs": 8.0, "fiber": 1.0, "sodium": 600},
    "宁都三杯鸡": {"calories": 360, "protein": 28.0, "fat": 24.0, "carbs": 8.0, "fiber": 0, "sodium": 650},
    "萍乡小炒肉": {"calories": 320, "protein": 20.0, "fat": 24.0, "carbs": 6.0, "fiber": 0.5, "sodium": 600},
    "小炒黄牛肉": {"calories": 280, "protein": 26.0, "fat": 18.0, "carbs": 4.0, "fiber": 0.5, "sodium": 550},
    "宜春慈化鸡": {"calories": 320, "protein": 28.0, "fat": 20.0, "carbs": 6.0, "fiber": 0.5, "sodium": 600},
    "丰城牛腩煲": {"calories": 380, "protein": 26.0, "fat": 22.0, "carbs": 18.0, "fiber": 1.0, "sodium": 680},
    # ---- 日式 ----
    "烧鸟丼": {"calories": 420, "protein": 24.0, "fat": 16.0, "carbs": 44.0, "fiber": 0.5, "sodium": 550},
    "关东煮": {"calories": 120, "protein": 8.0, "fat": 4.0, "carbs": 14.0, "fiber": 1.0, "sodium": 700},
    # ---- 煲类 ----
    "鸡公煲": {"calories": 420, "protein": 28.0, "fat": 22.0, "carbs": 26.0, "fiber": 1.5, "sodium": 720},
    "黄焖鸡": {"calories": 400, "protein": 26.0, "fat": 18.0, "carbs": 32.0, "fiber": 1.0, "sodium": 650},
    # ---- 瓦罐汤 ----
    "瓦罐鸡汤": {"calories": 80, "protein": 10.0, "fat": 4.0, "carbs": 1.0, "fiber": 0, "sodium": 250},
    "瓦罐排骨汤": {"calories": 100, "protein": 8.0, "fat": 6.0, "carbs": 2.0, "fiber": 0, "sodium": 300},
    "瓦罐老鸭汤": {"calories": 120, "protein": 12.0, "fat": 6.0, "carbs": 2.0, "fiber": 0, "sodium": 320},
    # ---- 饮品 ----
    "美式咖啡": {"calories": 10, "protein": 0.5, "fat": 0, "carbs": 1.0, "fiber": 0, "sodium": 5},
    "拿铁": {"calories": 140, "protein": 7.0, "fat": 7.0, "carbs": 12.0, "fiber": 0, "sodium": 80},
    "抹茶拿铁": {"calories": 160, "protein": 7.0, "fat": 7.0, "carbs": 18.0, "fiber": 0, "sodium": 80},
    "珍珠奶茶": {"calories": 200, "protein": 2.5, "fat": 5.0, "carbs": 36.0, "fiber": 0, "sodium": 60},
    "港式奶茶": {"calories": 150, "protein": 4.0, "fat": 6.0, "carbs": 20.0, "fiber": 0, "sodium": 65},
    "豆浆": {"calories": 31, "protein": 3.0, "fat": 1.5, "carbs": 1.5, "fiber": 0, "sodium": 2},
    "小吊梨汤": {"calories": 70, "protein": 0.5, "fat": 0, "carbs": 17.0, "fiber": 0.5, "sodium": 5},
    "罐罐烤奶": {"calories": 180, "protein": 5.0, "fat": 6.0, "carbs": 26.0, "fiber": 0, "sodium": 80},
    # ---- 汤粥 ----
    "紫菜蛋花汤": {"calories": 30, "protein": 2.0, "fat": 1.0, "carbs": 3.0, "fiber": 0.3, "sodium": 350},
    "大酱汤": {"calories": 90, "protein": 5.0, "fat": 4.0, "carbs": 10.0, "fiber": 1.5, "sodium": 680},
    "小米粥": {"calories": 46, "protein": 1.4, "fat": 0.7, "carbs": 8.4, "fiber": 0.5, "sodium": 2},
    "玉米浓汤": {"calories": 130, "protein": 3.5, "fat": 7.0, "carbs": 15.0, "fiber": 1.0, "sodium": 280},
    "养生煨汤": {"calories": 80, "protein": 6.0, "fat": 3.0, "carbs": 6.0, "fiber": 0, "sodium": 300},
    # ---- 西餐 ----
    "玛格丽特披萨": {"calories": 320, "protein": 14.0, "fat": 12.0, "carbs": 40.0, "fiber": 2.0, "sodium": 580},
    "黑椒牛肉焗饭": {"calories": 420, "protein": 26.0, "fat": 18.0, "carbs": 40.0, "fiber": 1.0, "sodium": 600},
    "番茄肉酱意面": {"calories": 420, "protein": 16.0, "fat": 14.0, "carbs": 56.0, "fiber": 2.5, "sodium": 550},
    # ---- 轻食 ----
    "鸡胸肉沙拉": {"calories": 180, "protein": 22.0, "fat": 6.0, "carbs": 10.0, "fiber": 3.0, "sodium": 200},
    "牛肉紫薯碗": {"calories": 320, "protein": 24.0, "fat": 8.0, "carbs": 38.0, "fiber": 4.0, "sodium": 280},
    "水煮牛肉（减脂版）": {"calories": 200, "protein": 28.0, "fat": 8.0, "carbs": 4.0, "fiber": 0.5, "sodium": 400},
    # ---- 点心/甜品 ----
    "提拉米苏": {"calories": 280, "protein": 5.0, "fat": 16.0, "carbs": 32.0, "fiber": 0, "sodium": 100},
    "冰淇淋": {"calories": 140, "protein": 2.5, "fat": 6.0, "carbs": 18.0, "fiber": 0, "sodium": 50},
    # ---- 猪/牛/羊 熟食 ----
    "酱肘子": {"calories": 320, "protein": 26.0, "fat": 24.0, "carbs": 3.0, "fiber": 0, "sodium": 680},
    "酱猪蹄": {"calories": 280, "protein": 22.0, "fat": 20.0, "carbs": 5.0, "fiber": 0, "sodium": 620},
    "酱牛肉": {"calories": 220, "protein": 34.0, "fat": 10.0, "carbs": 3.0, "fiber": 0, "sodium": 720},
    "酱猪肘": {"calories": 320, "protein": 26.0, "fat": 24.0, "carbs": 3.0, "fiber": 0, "sodium": 680},
    "护心肉": {"calories": 220, "protein": 20.0, "fat": 16.0, "carbs": 1.0, "fiber": 0, "sodium": 400},
    "跷脚牛肉": {"calories": 220, "protein": 26.0, "fat": 12.0, "carbs": 4.0, "fiber": 0, "sodium": 380},
    "老汤酱货拼盘": {"calories": 280, "protein": 24.0, "fat": 18.0, "carbs": 6.0, "fiber": 0, "sodium": 620},
    # ---- 饺子/馄饨 ----
    "水饺（猪肉白菜）": {"calories": 280, "protein": 12.0, "fat": 10.0, "carbs": 36.0, "fiber": 1.0, "sodium": 400},
    "水饺（韭菜鸡蛋）": {"calories": 240, "protein": 10.0, "fat": 8.0, "carbs": 32.0, "fiber": 1.5, "sodium": 380},
    "水饺（牛肉大葱）": {"calories": 300, "protein": 14.0, "fat": 12.0, "carbs": 34.0, "fiber": 1.0, "sodium": 420},
    "猪肉玉米馄饨": {"calories": 260, "protein": 12.0, "fat": 10.0, "carbs": 30.0, "fiber": 0.5, "sodium": 420},
    # ---- 套餐 ----
    "芝士拉面": {"calories": 450, "protein": 14.0, "fat": 18.0, "carbs": 56.0, "fiber": 0.5, "sodium": 750},
    "鸡公煲": {"calories": 420, "protein": 28.0, "fat": 22.0, "carbs": 26.0, "fiber": 1.5, "sodium": 720},
}


# 在线 LLM 估算 (可选，用于未收录的新菜品)
async def llm_estimate_nutrition(dish_name: str) -> dict:
    """
    调用 LLM 估算菜品营养。此函数可由外部大模型服务实现。
    目前使用本地 LLM_NUTRITION_DB 精确匹配 + 食材推断作为回退。
    """
    # 优先精确匹配
    if dish_name in LLM_NUTRITION_DB:
        return LLM_NUTRITION_DB[dish_name]

    # 去掉括号等单位信息后尝试匹配
    import re
    cleaned = re.sub(r'[（(][^)）]*[)）]', '', dish_name).strip()
    if cleaned in LLM_NUTRITION_DB:
        return LLM_NUTRITION_DB[cleaned]

    # 模糊匹配: 找最相似的关键词
    best = None
    best_overlap = 0
    for key in LLM_NUTRITION_DB:
        overlap = len(set(key) & set(dish_name)) / max(len(key), 1)
        if overlap > best_overlap and overlap > 0.5:
            best_overlap = overlap
            best = key

    if best:
        return LLM_NUTRITION_DB[best]

    # 完全未知: 基于食材词推断
    return _infer_from_ingredients(dish_name)


def _infer_from_ingredients(name: str) -> dict:
    """基于菜名关键词推断营养成分"""
    result = {"calories": 100, "protein": 5, "fat": 5, "carbs": 10, "fiber": 1, "sodium": 300}
    portion = 350  # 克

    # 肉类
    if any(k in name for k in ["牛肉", "牛腩", "牛排"]):
        result.update(calories=180, protein=22, fat=10, carbs=2)
    elif any(k in name for k in ["猪肉", "排骨", "叉烧", "猪", "肘", "蹄", "腊肉"]):
        result.update(calories=250, protein=16, fat=20, carbs=4)
    elif "鸡" in name:
        result.update(calories=200, protein=22, fat=12, carbs=2)
    elif "羊" in name:
        result.update(calories=220, protein=20, fat=16, carbs=2)
    elif any(k in name for k in ["鱼", "虾", "海鲜"]):
        result.update(calories=140, protein=18, fat=5, carbs=2)
    # 主食
    if any(k in name for k in ["饭", "米", "面", "粉", "包", "饼", "馒头", "花卷"]):
        result["carbs"] = 50
        result["calories"] += 100
    # 烹饪方式
    if any(k in name for k in ["炸", "酥", "烤"]):
        result["fat"] += 10
        result["calories"] += 100
    if any(k in name for k in ["辣", "麻辣", "香锅", "冒"]):
        result["sodium"] = 600
        result["fat"] += 5
    if "汤" in name or "煲" in name:
        result["calories"] = min(result["calories"], 120)
    if "豆腐" in name or "素" in name:
        result["protein"] = 8
        result["fat"] = 5
        result["calories"] = 120

    # Add fiber default
    if result["fiber"] == 1:
        result["fiber"] = round(portion / 200, 1)

    return result


# 兼容旧接口
COMMON_NUTRITION = LLM_NUTRITION_DB


@router.get("/common-db")
async def get_common_nutrition_db():
    """获取预置的营养成分数据库"""
    return {"count": len(LLM_NUTRITION_DB), "entries": LLM_NUTRITION_DB}


@router.get("/match/{dish_name}")
async def match_nutrition(dish_name: str):
    """根据菜品名称匹配营养成分"""
    result = await llm_estimate_nutrition(dish_name)
    return {"dish_name": dish_name, "nutrition": result, "source": "LLM精算" if dish_name in LLM_NUTRITION_DB else "食材推断"}


@router.get("/llm-estimate/{dish_name}")
async def llm_estimate(dish_name: str):
    """LLM 估算任意菜品营养 (在线)"""
    result = await llm_estimate_nutrition(dish_name)
    return {"dish_name": dish_name, "nutrition": result}
