App({
  globalData: {
    apiBase: 'http://localhost:8000/api',
    userInfo: null,
    token: null,
    history: [], // 搜索历史
    favorites: [], // 收藏的窗口/菜品
  },

  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }

    // 加载本地数据
    const history = wx.getStorageSync('searchHistory') || []
    const favorites = wx.getStorageSync('favorites') || []
    this.globalData.history = history
    this.globalData.favorites = favorites
  },

  // 微信登录
  login(callback) {
    wx.login({
      success: (res) => {
        if (res.code) {
          wx.request({
            url: `${this.globalData.apiBase}/users/login/wechat`,
            method: 'POST',
            data: { code: res.code },
            success: (response) => {
              if (response.data && response.data.access_token) {
                this.globalData.token = response.data.access_token
                this.globalData.userInfo = response.data.user
                wx.setStorageSync('token', response.data.access_token)
                wx.setStorageSync('userInfo', response.data.user)
                if (callback) callback(response.data.user)
              }
            },
          })
        }
      },
    })
  },

  // 添加搜索历史
  addSearchHistory(keyword) {
    let history = this.globalData.history
    history = history.filter((h) => h !== keyword)
    history.unshift(keyword)
    if (history.length > 20) history.pop()
    this.globalData.history = history
    wx.setStorageSync('searchHistory', history)
  },

  // 切换收藏
  toggleFavorite(type, id, name) {
    let favorites = this.globalData.favorites
    const idx = favorites.findIndex((f) => f.id === id && f.type === type)
    if (idx > -1) {
      favorites.splice(idx, 1)
    } else {
      favorites.push({ type, id, name })
    }
    this.globalData.favorites = favorites
    wx.setStorageSync('favorites', favorites)
    return idx === -1 // true = added, false = removed
  },

  isFavorite(type, id) {
    return this.globalData.favorites.some((f) => f.id === id && f.type === type)
  },
})
