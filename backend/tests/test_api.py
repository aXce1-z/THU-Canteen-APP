"""
清华大学食堂 API 测试

运行方式:
  cd backend
  pip install pytest pytest-asyncio httpx
  pytest tests/ -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """创建异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """测试健康检查"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    """测试根路径"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "清华食堂"


# ==================== 食堂 API ====================

@pytest.mark.asyncio
async def test_list_canteens_empty(client):
    """测试食堂列表（空数据库）"""
    response = await client.get("/api/canteens")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_create_and_get_canteen(client):
    """测试创建并获取食堂"""
    # Create
    payload = {
        "name": "测试食堂",
        "location": "测试位置",
        "opening_hours": {"早餐": "6:30-9:00", "午餐": "11:00-13:00"},
        "description": "这是一个测试食堂",
    }
    response = await client.post("/api/admin/canteens", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "测试食堂"
    assert created["location"] == "测试位置"
    canteen_id = created["id"]

    # Get
    response = await client.get(f"/api/canteens/{canteen_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试食堂"

    # Update
    response = await client.put(
        f"/api/admin/canteens/{canteen_id}",
        json={"name": "更新后的食堂", "location": "新位置"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的食堂"

    # Delete
    response = await client.delete(f"/api/admin/canteens/{canteen_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify deleted
    response = await client.get(f"/api/canteens/{canteen_id}")
    assert response.status_code == 404


# ==================== 窗口 API ====================

@pytest.mark.asyncio
async def test_create_and_get_window(client):
    """测试创建并获取窗口"""
    # First create a canteen
    c_resp = await client.post("/api/admin/canteens", json={
        "name": "窗口测试食堂", "location": "测试"
    })
    canteen_id = c_resp.json()["id"]

    # Create window
    payload = {
        "canteen_id": canteen_id,
        "name": "测试窗口",
        "window_number": "A01",
        "category": "小吃",
        "payment_methods": ["campus_card", "wechat"],
        "description": "测试窗口描述",
    }
    response = await client.post("/api/admin/windows", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "测试窗口"
    assert "wechat" in created["payment_methods"]
    window_id = created["id"]

    # Get
    response = await client.get(f"/api/windows/{window_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["canteen_name"] == "窗口测试食堂"

    # Filter by payment method
    response = await client.get("/api/windows?payment_method=wechat")
    assert response.status_code == 200
    assert response.json()["total"] >= 1

    # Delete
    response = await client.delete(f"/api/admin/windows/{window_id}")
    assert response.status_code == 200

    # Cleanup
    await client.delete(f"/api/admin/canteens/{canteen_id}")


# ==================== 菜品 API ====================

@pytest.mark.asyncio
async def test_create_and_get_dish(client):
    """测试创建并获取菜品"""
    # Setup
    c_resp = await client.post("/api/admin/canteens", json={"name": "菜品测试食堂"})
    canteen_id = c_resp.json()["id"]
    w_resp = await client.post("/api/admin/windows", json={
        "canteen_id": canteen_id, "name": "菜品测试窗口"
    })
    window_id = w_resp.json()["id"]

    # Create dish
    payload = {
        "window_id": window_id,
        "name": "生煎包",
        "category": "小吃",
        "price": 3.5,
        "unit": "个",
        "nutrition": {"calories": 270, "protein": 10.0, "fat": 13.0, "carbs": 29.0},
        "is_recommended": True,
    }
    response = await client.post("/api/admin/dishes", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "生煎包"
    assert float(created["price"]) == 3.5
    dish_id = created["id"]

    # Get
    response = await client.get(f"/api/dishes/{dish_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["canteen_name"] == "菜品测试食堂"

    # Get nutrition
    response = await client.get(f"/api/dishes/{dish_id}/nutrition")
    assert response.status_code == 200
    nutrition = response.json()
    assert nutrition["calories"] == 270

    # Cleanup
    await client.delete(f"/api/admin/dishes/{dish_id}")
    await client.delete(f"/api/admin/windows/{window_id}")
    await client.delete(f"/api/admin/canteens/{canteen_id}")


# ==================== 搜索 API ====================

@pytest.mark.asyncio
async def test_search(client):
    """测试搜索"""
    # Setup: create canteen, window, dish
    c_resp = await client.post("/api/admin/canteens", json={"name": "搜索测试食堂"})
    canteen_id = c_resp.json()["id"]
    w_resp = await client.post("/api/admin/windows", json={
        "canteen_id": canteen_id, "name": "搜索测试窗口"
    })
    window_id = w_resp.json()["id"]

    dishes_to_create = [
        ("生煎包", "小吃", 3.5),
        ("小笼包", "小吃", 8.0),
        ("宫保鸡丁", "炒菜", 12.0),
    ]
    for name, cat, price in dishes_to_create:
        await client.post("/api/admin/dishes", json={
            "window_id": window_id, "name": name, "category": cat, "price": price
        })

    # Search by name
    response = await client.get("/api/search?q=生煎")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 1
    assert len(data["dishes"]) >= 1
    assert data["dishes"][0]["name"] == "生煎包"

    # Search suggestions
    response = await client.get("/api/search/suggestions?q=宫保")
    assert response.status_code == 200
    data = response.json()
    assert "宫保鸡丁" in data["suggestions"]

    # Cleanup
    await client.delete(f"/api/admin/windows/{window_id}")
    await client.delete(f"/api/admin/canteens/{canteen_id}")


# ==================== 评价 API ====================

@pytest.mark.asyncio
async def test_create_and_get_review(client):
    """测试创建并获取评价"""
    # Setup
    c_resp = await client.post("/api/admin/canteens", json={"name": "评价测试食堂"})
    canteen_id = c_resp.json()["id"]
    w_resp = await client.post("/api/admin/windows", json={
        "canteen_id": canteen_id, "name": "评价测试窗口"
    })
    window_id = w_resp.json()["id"]
    d_resp = await client.post("/api/admin/dishes", json={
        "window_id": window_id, "name": "评价测试菜品", "price": 10.0
    })
    dish_id = d_resp.json()["id"]

    # Create review
    payload = {
        "window_id": window_id,
        "dish_id": dish_id,
        "rating": 5,
        "content": "非常好吃！强烈推荐！",
        "tags": ["口味好", "分量足"],
    }
    response = await client.post(f"/api/reviews/windows/{window_id}", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["rating"] == 5
    review_id = created["id"]

    # Get window reviews
    response = await client.get(f"/api/reviews/windows/{window_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Get dish reviews
    response = await client.get(f"/api/reviews/dishes/{dish_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Like review
    response = await client.post(f"/api/reviews/{review_id}/like")
    assert response.status_code == 200
    assert response.json()["like_count"] == 1

    # Cleanup
    await client.delete(f"/api/admin/dishes/{dish_id}")
    await client.delete(f"/api/admin/windows/{window_id}")
    await client.delete(f"/api/admin/canteens/{canteen_id}")


# ==================== 营养分析 API ====================

@pytest.mark.asyncio
async def test_nutrition_analysis(client):
    """测试营养分析"""
    # Test common nutrition DB
    response = await client.get("/api/nutrition/common-db")
    assert response.status_code == 200
    data = response.json()
    assert "生煎包" in data
    assert data["生煎包"]["calories"] == 270

    # Test nutrition matching
    response = await client.get("/api/nutrition/match/红烧肉")
    assert response.status_code == 200
    data = response.json()
    assert "红烧肉" in data["matches"]


@pytest.mark.asyncio
async def test_combined_nutrition(client):
    """测试组合餐营养分析"""
    # Setup
    c_resp = await client.post("/api/admin/canteens", json={"name": "营养测试食堂"})
    canteen_id = c_resp.json()["id"]
    w_resp = await client.post("/api/admin/windows", json={
        "canteen_id": canteen_id, "name": "营养测试窗口"
    })
    window_id = w_resp.json()["id"]

    # Create two dishes with nutrition
    d1_resp = await client.post("/api/admin/dishes", json={
        "window_id": window_id, "name": "米饭", "price": 0.5,
        "nutrition": {"calories": 116, "protein": 2.6, "fat": 0.3, "carbs": 25.9},
    })
    d2_resp = await client.post("/api/admin/dishes", json={
        "window_id": window_id, "name": "宫保鸡丁", "price": 12.0,
        "nutrition": {"calories": 190, "protein": 18.0, "fat": 11.0, "carbs": 6.0},
    })
    dish1_id = d1_resp.json()["id"]
    dish2_id = d2_resp.json()["id"]

    # Analyze
    response = await client.post("/api/nutrition/analyze", json={
        "dish_ids": [dish1_id, dish2_id]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["calories"] == 306  # 116 + 190
    assert data["protein"] == 20.6  # 2.6 + 18.0
    assert data["carbs"] == 31.9  # 25.9 + 6.0

    # Cleanup
    await client.delete(f"/api/admin/windows/{window_id}")
    await client.delete(f"/api/admin/canteens/{canteen_id}")


@pytest.mark.asyncio
async def test_hot_dishes(client):
    """测试热门菜品接口"""
    response = await client.get("/api/dishes/hot")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_pagination(client):
    """测试分页"""
    # Create several canteens
    ids = []
    for i in range(5):
        resp = await client.post("/api/admin/canteens", json={
            "name": f"分页测试食堂{i}", "location": "测试"
        })
        ids.append(resp.json()["id"])

    # Test pagination
    response = await client.get("/api/canteens?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) <= 2

    # Cleanup
    for cid in ids:
        await client.delete(f"/api/admin/canteens/{cid}")
