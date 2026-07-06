"""
清华大学校园卡交易记录解析器

校园卡交易导出格式 (card.tsinghua.edu.cn/userselftrade):
  交易时间, 交易金额, 商户名称, 交易类型, 卡余额
  e.g. "2025-09-15 11:35, -12.50, 紫荆园一层, 消费, 85.30"

支持 CSV 和 Excel 格式导入。
"""
import csv
import io
import re
from datetime import datetime, date
from collections import defaultdict


# 商户名 → 食堂 关键词映射
CANTEEN_KEYWORDS = {
    "紫荆园": ["紫荆", "紫荆园"],
    "桃李园": ["桃李", "桃李园"],
    "清芬园": ["清芬", "清芬园"],
    "听涛园": ["听涛", "听涛园"],
    "丁香园": ["丁香", "丁香园"],
    "观畴园": ["观畴", "观畴园", "万人"],
    "芝兰园": ["芝兰", "芝兰园"],
    "玉树园": ["玉树", "玉树园"],
    "荷园": ["荷园"],
    "澜园": ["澜园"],
    "寓园": ["寓园"],
    "南园": ["南园"],
    "家园": ["家园"],
    "北园": ["北园"],
    "融园": ["融园"],
    "熙春园": ["熙春", "熙春园"],
    "清青": ["清青"],  # 归为"清青系列"
}


def match_canteen(merchant: str) -> str:
    """根据商户名匹配食堂"""
    for canteen, keywords in CANTEEN_KEYWORDS.items():
        for kw in keywords:
            if kw in merchant:
                return canteen
    return "其他"


def guess_meal_time(hour: int) -> str:
    """根据时间推测餐次"""
    if 6 <= hour < 10:
        return "早餐"
    elif 10 <= hour < 14:
        return "午餐"
    elif 16 <= hour < 20:
        return "晚餐"
    elif 20 <= hour < 24:
        return "夜宵"
    return "其他"


def parse_csv(content: bytes) -> dict:
    """解析 CSV 内容，返回结构化日记数据"""
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))

    # 尝试自动检测表头
    rows = list(reader)
    if not rows:
        return {"error": "文件为空"}

    # 跳过表头行（如果第一行包含中文）
    start = 0
    header = rows[0]
    if any("一" <= (c or "")[0:1] <= "鿿" for c in header if c):
        start = 1

    records = []
    total_spent = 0.0
    canteen_stats = defaultdict(lambda: {"count": 0, "amount": 0.0})
    daily_stats = defaultdict(lambda: {"count": 0, "amount": 0.0})

    for row in rows[start:]:
        if len(row) < 2:
            continue
        try:
            time_str = str(row[0]).strip()
            amount_str = str(row[1]).strip().replace(",", "")
            merchant = str(row[2]).strip() if len(row) > 2 else ""

            # 跳过头尾行和非消费记录
            if "时间" in time_str or "合计" in time_str or "小计" in time_str:
                continue
            if not merchant:
                continue

            # 解析金额（负数表示支出）
            amount = float(amount_str)
            if amount >= 0:
                continue  # 跳过充值/退款，只看消费

            amount = abs(amount)

            # 解析时间
            dt = None
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"]:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    break
                except ValueError:
                    continue

            if dt is None:
                continue

            canteen = match_canteen(merchant)
            meal = guess_meal_time(dt.hour)
            day_key = dt.strftime("%Y-%m-%d")

            records.append({
                "time": dt.strftime("%Y-%m-%d %H:%M"),
                "amount": round(amount, 2),
                "merchant": merchant,
                "canteen": canteen,
                "meal": meal,
            })

            total_spent += amount
            canteen_stats[canteen]["count"] += 1
            canteen_stats[canteen]["amount"] += amount
            daily_stats[day_key]["count"] += 1
            daily_stats[day_key]["amount"] += amount

        except (ValueError, IndexError):
            continue

    if not records:
        return {"error": "未能解析到有效消费记录"}

    # 按日期排序
    sorted_days = sorted(daily_stats.items())
    sorted_canteens = sorted(canteen_stats.items(),
                              key=lambda x: x[1]["amount"], reverse=True)

    return {
        "total_records": len(records),
        "total_spent": round(total_spent, 2),
        "days_covered": len(sorted_days),
        "canteens": [
            {"name": name, "count": s["count"], "amount": round(s["amount"], 2)}
            for name, s in sorted_canteens
        ],
        "daily": [
            {"date": day, "count": s["count"], "amount": round(s["amount"], 2)}
            for day, s in sorted_days
        ],
        "records": records[:50],  # 只返回前50条明细
    }
