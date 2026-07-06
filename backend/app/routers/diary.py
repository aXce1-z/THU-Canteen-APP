"""饮食日记 API"""
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.services.card_parser import parse_csv

router = APIRouter(prefix="/diary", tags=["饮食日记"])


class DiaryStats(BaseModel):
    total_records: int
    total_spent: float
    days_covered: int
    canteens: list
    daily: list
    records: list
    error: str | None = None


@router.post("/import", response_model=DiaryStats)
async def import_card_records(file: UploadFile = File(...)):
    """导入校园卡交易记录文件（CSV/Excel）"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")

    # 支持 CSV 和 Excel
    if file.filename.endswith(('.csv', '.CSV')):
        result = parse_csv(content)
    elif file.filename.endswith(('.xlsx', '.xls')):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb.active
        # 转为 CSV 格式再解析
        csv_lines = []
        for row in ws.iter_rows(values_only=True):
            csv_lines.append(",".join(str(c or "") for c in row))
        result = parse_csv("\n".join(csv_lines).encode("utf-8"))
    else:
        raise HTTPException(status_code=400, detail="仅支持 CSV 或 Excel 文件")

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return DiaryStats(**result)
