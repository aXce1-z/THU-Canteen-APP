const { getDish, getDishNutrition, getDishReviews } = require('../../utils/api')

Page({
  data: {
    dish: null, nutrition: null, reviews: [],
    loading: true, isFav: false,
  },

  onLoad(options) {
    this.dishId = options.id
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [dish, nutrition, reviewRes] = await Promise.all([
        getDish(this.dishId), getDishNutrition(this.dishId),
        getDishReviews(this.dishId, { page_size: 20 }),
      ])
      const app = getApp()
      this.setData({
        dish, nutrition, reviews: reviewRes.items || [],
        loading: false, isFav: app.isFavorite('dish', this.dishId),
      })
    } catch (e) {
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  onTapWindow() {
    wx.navigateTo({ url: `/pages/window/detail?id=${this.data.dish.window_id}&name=${this.data.dish.window_name}` })
  },

  onWriteReview() {
    wx.navigateTo({ url: `/pages/review/create?windowId=${this.data.dish.window_id}&windowName=${this.data.dish.window_name}&dishId=${this.dishId}&dishName=${this.data.dish.name}` })
  },

  onAddToNutrition() {
    let selected = wx.getStorageSync('nutritionDishes') || []
    if (selected.find(d => d.id === this.dishId)) {
      wx.showToast({ title: '已在分析列表中', icon: 'none' })
      return
    }
    selected.push({ id: this.dishId, name: this.data.dish.name, price: this.data.dish.price, nutrition: this.data.nutrition })
    wx.setStorageSync('nutritionDishes', selected)
    wx.showToast({ title: '已加入', icon: 'success' })
  },

  onToggleFavorite() {
    const app = getApp()
    const added = app.toggleFavorite('dish', this.data.dish.id, this.data.dish.name)
    this.setData({ isFav: added })
    wx.showToast({ title: added ? '已收藏' : '已取消', icon: 'none' })
  },
})
