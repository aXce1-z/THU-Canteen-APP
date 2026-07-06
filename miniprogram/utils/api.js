const app = getApp()

const API_BASE = app.globalData.apiBase || 'http://localhost:8000/api'

/**
 * 封装请求
 */
function request(url, options = {}) {
  const token = wx.getStorageSync('token')

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE}${url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {}),
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          wx.showToast({
            title: res.data.detail || '请求失败',
            icon: 'none',
          })
          reject(res)
        }
      },
      fail(err) {
        wx.showToast({
          title: '网络错误，请检查网络连接',
          icon: 'none',
        })
        reject(err)
      },
    })
  })
}

// ==================== 食堂 ====================
export function getCanteens(params = {}) {
  const qs = Object.keys(params).map(k => `${k}=${params[k]}`).join('&')
  return request(`/canteens?${qs}`)
}

export function getCanteen(id) {
  return request(`/canteens/${id}`)
}

export function getCanteenWindows(canteenId, params = {}) {
  const qs = Object.keys(params).map(k => `${k}=${params[k]}`).join('&')
  return request(`/canteens/${canteenId}/windows?${qs}`)
}

// ==================== 窗口 ====================
export function getWindows(params = {}) {
  const qs = Object.keys(params).map(k => `${k}=${params[k]}`).join('&')
  return request(`/windows?${qs}`)
}

export function getWindow(id) {
  return request(`/windows/${id}`)
}

export function getWindowDishes(windowId, params = {}) {
  const qs = Object.keys(params).map(k => `${k}=${params[k]}`).join('&')
  return request(`/windows/${windowId}/dishes?${qs}`)
}

// ==================== 菜品 ====================
export function getDishes(params = {}) {
  const qs = Object.keys(params).map(k => `${k}=${params[k]}`).join('&')
  return request(`/dishes?${qs}`)
}

export function getDish(id) {
  return request(`/dishes/${id}`)
}

export function getHotDishes(limit = 10) {
  return request(`/dishes/hot?limit=${limit}`)
}

// ==================== 搜索 ====================
export function search(q, params = {}) {
  const query = { q, ...params }
  const qs = Object.keys(query).map(k => `${k}=${encodeURIComponent(query[k])}`).join('&')
  return request(`/search?${qs}`)
}

export function getSuggestions(q) {
  return request(`/search/suggestions?q=${encodeURIComponent(q)}`)
}

// ==================== 评价 ====================
export function getWindowReviews(windowId, params = {}) {
  const qs = Object.keys(params).map(k => `${k}=${params[k]}`).join('&')
  return request(`/reviews/windows/${windowId}?${qs}`)
}

export function getDishReviews(dishId, params = {}) {
  const qs = Object.keys(params).map(k => `${k}=${params[k]}`).join('&')
  return request(`/reviews/dishes/${dishId}?${qs}`)
}

export function createReview(windowId, data) {
  return request(`/reviews/windows/${windowId}`, {
    method: 'POST',
    data,
  })
}

export function likeReview(reviewId) {
  return request(`/reviews/${reviewId}/like`, { method: 'POST' })
}

// ==================== 营养分析 ====================
export function getDishNutrition(dishId) {
  return request(`/dishes/${dishId}/nutrition`)
}

export function analyzeNutrition(dishIds) {
  return request('/nutrition/analyze', {
    method: 'POST',
    data: { dish_ids: dishIds },
  })
}

export function getCommonNutritionDb() {
  return request('/nutrition/common-db')
}

// ==================== 用户 ====================
export function getUserProfile() {
  return request('/users/me')
}
