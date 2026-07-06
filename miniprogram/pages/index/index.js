const { getCanteens, getHotDishes } = require('../../utils/api')

Page({
  data: {
    canteens: [],
    hotDishes: [],
    searchKeyword: '',
    paymentFilter: '',
    loading: true,
  },

  onShow() {
    if (this.data.canteens.length === 0) {
      this.loadData()
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [canteenRes, hotRes] = await Promise.all([
        getCanteens({ page_size: 20 }),
        getHotDishes(8),
      ])
      this.setData({
        canteens: canteenRes.items || [],
        hotDishes: hotRes || [],
        loading: false,
      })
    } catch (e) {
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  onSearch() {
    const kw = this.data.searchKeyword.trim()
    if (kw) {
      getApp().addSearchHistory(kw)
      wx.navigateTo({ url: `/pages/search/index?keyword=${encodeURIComponent(kw)}` })
    }
  },

  onSearchInput(e) {
    this.setData({ searchKeyword: e.detail.value })
  },

  onTapCanteen(e) {
    const { id, name } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/canteen/detail?id=${id}&name=${name}` })
  },

  onTapDish(e) {
    wx.navigateTo({ url: `/pages/dish/detail?id=${e.currentTarget.dataset.id}` })
  },

  onFilterPayment(e) {
    const method = e.currentTarget.dataset.method
    const active = this.data.paymentFilter === method ? '' : method
    this.setData({ paymentFilter: active })
    wx.navigateTo({ url: `/pages/search/index?payment=${method}` })
  },
})
