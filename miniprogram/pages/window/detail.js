const { getWindow, getWindowDishes, getWindowReviews } = require('../../utils/api')

Page({
  data: {
    window: null, dishes: [], reviews: [],
    activeTab: 'dishes', loading: true, isFav: false,
  },

  onLoad(options) {
    const { id, name } = options
    if (name) wx.setNavigationBarTitle({ title: name })
    this.windowId = id
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [window, dishRes, reviewRes] = await Promise.all([
        getWindow(this.windowId),
        getWindowDishes(this.windowId, { page_size: 100 }),
        getWindowReviews(this.windowId, { page_size: 20 }),
      ])
      const app = getApp()
      this.setData({
        window, dishes: dishRes.items || [], reviews: reviewRes.items || [],
        loading: false, isFav: app.isFavorite('window', this.windowId),
      })
    } catch (e) {
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  onSwitchTab(e) { this.setData({ activeTab: e.currentTarget.dataset.tab }) },

  onTapDish(e) { wx.navigateTo({ url: `/pages/dish/detail?id=${e.currentTarget.dataset.id}` }) },

  onWriteReview() {
    wx.navigateTo({ url: `/pages/review/create?windowId=${this.windowId}&windowName=${this.data.window.name}` })
  },

  onToggleFavorite() {
    const app = getApp()
    const added = app.toggleFavorite('window', this.data.window.id, this.data.window.name)
    this.setData({ isFav: added })
    wx.showToast({ title: added ? '已收藏' : '已取消', icon: 'none' })
  },
})
