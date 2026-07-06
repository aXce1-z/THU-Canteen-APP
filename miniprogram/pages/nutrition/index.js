const { analyzeNutrition } = require('../../utils/api')

Page({
  data: {
    selectedDishes: [],
    nutritionResult: null,
    dailyReference: {
      calories: 2200,
      protein: 65,
      fat: 60,
      carbs: 300,
      fiber: 25,
      sodium: 2000,
    },
    analyzing: false,
  },

  onShow() {
    this.loadSelectedDishes()
  },

  loadSelectedDishes() {
    const dishes = wx.getStorageSync('nutritionDishes') || []
    this.setData({ selectedDishes: dishes })
  },

  // 删除菜品
  onRemoveDish(e) {
    const idx = e.currentTarget.dataset.index
    const dishes = this.data.selectedDishes
    dishes.splice(idx, 1)
    wx.setStorageSync('nutritionDishes', dishes)
    this.setData({ selectedDishes: dishes, nutritionResult: null })
  },

  // 清空
  onClearAll() {
    wx.setStorageSync('nutritionDishes', [])
    this.setData({ selectedDishes: [], nutritionResult: null })
  },

  // 开始分析
  async onAnalyze() {
    if (this.data.selectedDishes.length === 0) {
      wx.showToast({ title: '请先添加菜品', icon: 'none' })
      return
    }

    this.setData({ analyzing: true })
    try {
      const dishIds = this.data.selectedDishes.map(d => d.id)
      const result = await analyzeNutrition(dishIds)
      this.setData({ nutritionResult: result })
    } catch (e) {
      console.error('分析失败', e)
    } finally {
      this.setData({ analyzing: false })
    }
  },

  // 计算百分比
  getPercent(value, ref) {
    if (!value || !ref) return 0
    return Math.min(Math.round((value / ref) * 100), 100)
  },

  // 查看添加建议
  getAdvice() {
    const r = this.data.nutritionResult
    const ref = this.data.dailyReference
    if (!r) return ''

    const advice = []
    if (r.calories < ref.calories * 0.3) advice.push('热量偏低，可以再加个主食')
    if (r.protein < ref.protein * 0.3) advice.push('蛋白质不足，建议添加肉类或豆制品')
    if (r.fat > ref.fat * 0.4) advice.push('脂肪偏高，注意搭配蔬菜')
    if (r.carbs < ref.carbs * 0.25) advice.push('碳水偏低，建议加点主食')

    if (advice.length === 0) {
      if (r.calories < ref.calories * 0.6) {
        advice.push('营养搭配不错，还可以再吃一点')
      } else {
        advice.push('营养搭配均衡，这顿饭很健康！')
      }
    }

    return advice.join('；')
  },
})
