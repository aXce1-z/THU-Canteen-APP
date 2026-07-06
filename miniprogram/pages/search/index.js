const { search, getSuggestions } = require('../../utils/api')

Page({
  data: {
    keyword: '',
    results: null,
    suggestions: [],
    history: [],
    sortBy: 'relevance',
    searching: false,
    hasSearched: false,
  },

  onLoad(options) {
    // 加载搜索历史
    const app = getApp()
    this.setData({ history: app.globalData.history || [] })

    // 如果携带参数直接搜索
    if (options.keyword) {
      this.setData({ keyword: options.keyword })
      this.doSearch()
    }
    if (options.payment) {
      this.setData({ keyword: '' })
      this.paymentFilter = options.payment
    }
  },

  // 搜索输入
  onInput(e) {
    const val = e.detail.value
    this.setData({ keyword: val })
    if (val.length >= 1) {
      this.getSuggestionsDebounced(val)
    } else {
      this.setData({ suggestions: [] })
    }
  },

  // 防抖获取建议
  getSuggestionsDebounced(val) {
    if (this.suggestTimer) clearTimeout(this.suggestTimer)
    this.suggestTimer = setTimeout(async () => {
      try {
        const res = await getSuggestions(val)
        this.setData({ suggestions: res.suggestions || [] })
      } catch { /* ignore */ }
    }, 300)
  },

  // 执行搜索
  async doSearch() {
    const kw = this.data.keyword.trim()
    if (!kw) return

    this.setData({ searching: true, hasSearched: true, suggestions: [] })

    // 添加到历史
    const app = getApp()
    app.addSearchHistory(kw)
    this.setData({ history: app.globalData.history })

    try {
      const params = { sort: this.data.sortBy }
      if (this.paymentFilter) params.payment_method = this.paymentFilter
      const res = await search(kw, params)
      this.setData({ results: res })
    } catch (e) {
      console.error('搜索失败', e)
    } finally {
      this.setData({ searching: false })
    }
  },

  onSearch() {
    this.doSearch()
  },

  onClear() {
    this.setData({ keyword: '', results: null, suggestions: [], hasSearched: false })
  },

  // 点击建议
  onTapSuggestion(e) {
    const kw = e.currentTarget.dataset.keyword
    this.setData({ keyword: kw })
    this.doSearch()
  },

  // 点击历史
  onTapHistory(e) {
    const kw = e.currentTarget.dataset.keyword
    this.setData({ keyword: kw })
    this.doSearch()
  },

  // 清除历史
  onClearHistory() {
    const app = getApp()
    app.globalData.history = []
    wx.removeStorageSync('searchHistory')
    this.setData({ history: [] })
  },

  // 排序
  onSort(e) {
    const sort = e.currentTarget.dataset.sort
    this.setData({ sortBy: sort })
    this.doSearch()
  },

  // 跳转菜品
  onTapDish(e) {
    wx.navigateTo({ url: `/pages/dish/detail?id=${e.currentTarget.dataset.id}` })
  },

  // 跳转窗口
  onTapWindow(e) {
    wx.navigateTo({ url: `/pages/window/detail?id=${e.currentTarget.dataset.id}` })
  },

  getPaymentLabel(m) {
    const map = { campus_card: '校园卡', wechat: '微信', alipay: '支付宝' }
    return map[m] || m
  },
})
