import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      window.location.href = '/login'
      return Promise.reject(error)
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// ==================== Canteens ====================
export const getCanteens = (params) => api.get('/canteens', { params })
export const getCanteen = (id) => api.get(`/canteens/${id}`)
export const createCanteen = (data) => api.post('/admin/canteens', data)
export const updateCanteen = (id, data) => api.put(`/admin/canteens/${id}`, data)
export const deleteCanteen = (id) => api.delete(`/admin/canteens/${id}`)

// ==================== Windows ====================
export const getWindows = (params) => api.get('/windows', { params })
export const getWindow = (id) => api.get(`/windows/${id}`)
export const createWindow = (data) => api.post('/admin/windows', data)
export const updateWindow = (id, data) => api.put(`/admin/windows/${id}`, data)
export const deleteWindow = (id) => api.delete(`/admin/windows/${id}`)
export const getCanteenWindows = (canteenId, params) => api.get(`/canteens/${canteenId}/windows`, { params })

// ==================== Dishes ====================
export const getDishes = (params) => api.get('/dishes', { params })
export const getWindowDishes = (windowId, params) => api.get(`/windows/${windowId}/dishes`, { params })
export const createDish = (data) => api.post('/admin/dishes', data)
export const updateDish = (id, data) => api.put(`/admin/dishes/${id}`, data)
export const deleteDish = (id) => api.delete(`/admin/dishes/${id}`)
export const batchImportDishes = (windowId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/admin/dishes/batch?window_id=${windowId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ==================== Reviews ====================
export const getWindowReviews = (windowId, params) => api.get(`/reviews/windows/${windowId}`, { params })
export const getDishReviews = (dishId, params) => api.get(`/reviews/dishes/${dishId}`, { params })

// ==================== Nutrition ====================
export const getCommonNutritionDb = () => api.get('/nutrition/common-db')
export const matchNutrition = (name) => api.get(`/nutrition/match/${name}`)

// ==================== Search ====================
export const searchAll = (params) => api.get('/search', { params })

export default api
