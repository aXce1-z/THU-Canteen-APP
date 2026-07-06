const { getCanteen, getCanteenWindows } = require('../../utils/api')

Page({
  data: {
    canteen: null,
    windows: [],
    filteredWindows: [],
    activeFilter: '',
    loading: true,
  },

  onLoad(options) {
    const { id, name } = options
    if (name) wx.setNavigationBarTitle({ title: name })
    this.canteenId = id
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const [canteen, winRes] = await Promise.all([
        getCanteen(this.canteenId),
        getCanteenWindows(this.canteenId, { page_size: 100 }),
      ])
      this.setData({
        canteen,
        windows: winRes.items || [],
        filteredWindows: winRes.items || [],
      })
    } catch (e) {
      console.error('加载失败', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  // 筛选分类
  onFilter(e) {
    const cat = e.currentTarget.dataset.category
    const active = this.data.activeFilter === cat ? '' : cat
    const filtered = active
      ? this.data.windows.filter(w => w.category === active)
      : this.data.windows
    this.setData({ activeFilter: active, filteredWindows: filtered })
  },

  // 跳转窗口详情
  onTapWindow(e) {
    const { id, name } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/window/detail?id=${id}&name=${name}` })
  },

  // 支付方式标识
  getPaymentLabel(methods) {
    if (!methods || methods.length === 0) return '仅校园卡'
    const hasWechat = methods.includes('wechat')
    const hasAlipay = methods.includes('alipay')
    if (hasWechat && hasAlipay) return '支持微信/支付宝'
    if (hasWechat) return '支持微信'
    if (hasAlipay) return '支持支付宝'
    return '仅校园卡'
  },

  // 收藏
  onToggleFavorite() {
    const app = getApp()
    const added = app.toggleFavorite('canteen', this.data.canteen.id, this.data.canteen.name)
    wx.showToast({ title: added ? '已收藏' : '已取消', icon: 'none' })
  },
})
