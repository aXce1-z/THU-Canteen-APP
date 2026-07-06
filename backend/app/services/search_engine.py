"""
基于 SQLite FTS5 + jieba 的全文搜索引擎
支持中文分词、同义词扩展、模糊匹配
"""
import os
import sqlite3
from typing import Optional

import jieba

# 同义词映射 (搜索时自动扩展)
SYNONYMS = {
    "西红柿": ["番茄", "西红柿"],
    "番茄": ["西红柿", "番茄"],
    "土豆": ["土豆", "马铃薯", "洋芋"],
    "马铃薯": ["土豆", "马铃薯", "洋芋"],
    "洋芋": ["土豆", "马铃薯", "洋芋"],
    "鸡蛋": ["鸡蛋", "蛋"],
    "蛋炒饭": ["蛋炒饭", "炒饭"],
    "生煎": ["生煎", "煎包", "生煎包"],
    "煎包": ["生煎", "煎包", "生煎包"],
    "包子": ["包子", "包", "小笼包"],
    "饺子": ["饺子", "水饺", "饺"],
    "面条": ["面条", "面"],
    "米饭": ["米饭", "饭"],
    "红薯": ["红薯", "地瓜", "番薯"],
    "米粉": ["米粉", "米线", "粉"],
    "馄饨": ["馄饨", "抄手", "云吞"],
    "抄手": ["馄饨", "抄手", "云吞"],
    "猪": ["猪", "猪肉"],
    "牛": ["牛", "牛肉"],
    "鸡": ["鸡", "鸡肉"],
    "鱼": ["鱼", "鱼肉"],
}


def _expand_query(query: str) -> str:
    """扩展查询词：将同义词加入搜索"""
    words = list(jieba.cut(query))
    expanded = set(words)
    for w in words:
        if w in SYNONYMS:
            expanded.update(SYNONYMS[w])
    return " OR ".join(expanded)

# 数据库路径（与 async 数据库相同文件）
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "thucanteen.db")


def _get_conn():
    return sqlite3.connect(DB_PATH)


def build_index():
    """构建 FTS5 全文搜索索引"""
    conn = _get_conn()
    try:
        # 删除旧的索引（如果 schema 变更）
        conn.execute("DROP TABLE IF EXISTS dish_fts")
        # 创建独立的 FTS5 表
        conn.execute("""
            CREATE VIRTUAL TABLE dish_fts USING fts5(
                name, window_name, canteen_name, category,
                tokenize='unicode61'
            )
        """)

        # 清空重建
        conn.execute("DELETE FROM dish_fts")

        # 从 dishes 表读取数据并插入 FTS 索引
        rows = conn.execute("""
            SELECT d.id as rowid, d.name, w.name, c.name, d.category
            FROM dishes d
            JOIN windows w ON d.window_id = w.id
            JOIN canteens c ON w.canteen_id = c.id
            WHERE d.is_available = 1
        """).fetchall()

        for row in rows:
            rowid, name, win_name, can_name, category = row
            # jieba 分词后拼接
            tokens = []
            for text in [name, win_name, can_name, category or ""]:
                tokens.extend(jieba.cut(text))
            tokenized = " ".join(tokens)

            conn.execute(
                "INSERT INTO dish_fts(rowid, name, window_name, canteen_name, category) VALUES (?, ?, ?, ?, ?)",
                (rowid, tokenized, " ".join(jieba.cut(win_name or "")),
                 " ".join(jieba.cut(can_name or "")), " ".join(jieba.cut(category or "")))
            )

        conn.commit()
        print(f"   [FTS] 索引 {len(rows)} 个菜品完成")
    finally:
        conn.close()


def search(query: str, canteen_id: Optional[str] = None,
           category: Optional[str] = None, limit: int = 20) -> list[str]:
    """全文搜索，返回匹配的 dish ID 列表"""
    conn = _get_conn()
    try:
        # 检查索引是否存在
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dish_fts'").fetchall()
        if not tables:
            return []

        # jieba 分词 + 同义词扩展
        fts_query = _expand_query(query)

        conditions = ["dish_fts MATCH ?"]
        params = [fts_query]

        if canteen_id:
            conditions.append("dish_fts.canteen_name IN (SELECT name FROM canteens WHERE id = ?)")
            params.append(canteen_id)

        sql = f"""
            SELECT rowid FROM dish_fts
            WHERE {' AND '.join(conditions)}
            ORDER BY rank
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [str(r[0]) for r in rows]
    except Exception:
        # FTS query might fail on special characters
        return []
    finally:
        conn.close()


def get_suggestions(query: str, limit: int = 8) -> list[str]:
    """获取搜索建议"""
    conn = _get_conn()
    try:
        tokens = list(jieba.cut(query))
        if not tokens:
            return []

        suggestions = set()
        for token in tokens:
            rows = conn.execute(
                "SELECT DISTINCT name FROM dishes WHERE name LIKE ? LIMIT ?",
                (f"%{token}%", limit)
            ).fetchall()
            suggestions.update(r[0] for r in rows)

        return list(suggestions)[:limit]
    finally:
        conn.close()
