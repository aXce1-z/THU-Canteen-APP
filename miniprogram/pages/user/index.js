Page({
  data: {
    userInfo: null,
    isLoggedIn: false,
    favorites: [],
    contributionCount: 0,
  },

  onShow() {
    const app = getApp()
    const userInfo = wx.getStorageSync('userInfo')
    const favorites = wx.getStorageSync('favorites') || []

    this.setData({
      userInfo,
      isLoggedIn: !!userInfo,
      favorites,
    })
  },

  // 登录
  onLogin() {
    const app = getApp()
    app.login((user) => {
      this.setData({
        userInfo: user,
        isLoggedIn: true,
      })
      wx.showToast({ title: '登录成功', icon: 'success' })
    })
  },

  // 跳转收藏
  onTapFavorite(e) {
    const { type, id, name } = e.currentTarget.dataset
    if (type === 'window') {
      wx.navigateTo({ url: `/pages/window/detail?id=${id}&name=${name}` })
    } else if (type === 'dish') {
      wx.navigateTo({ url: `/pages/dish/detail?id=${id}` })
    } else if (type === 'canteen') {
      wx.navigateTo({ url: `/pages/canteen/detail?id=${id}&name=${name}` })
    }
  },

  // 清除收藏
  onClearFavorites() {
    wx.showModal({
      title: '确认清除',
      content: '确定清除所有收藏？',
      success: (res) => {
        if (res.confirm) {
          const app = getApp()
          app.globalData.favorites = []
          wx.removeStorageSync('favorites')
          this.setData({ favorites: [] })
        }
      },
    })
  },

  // 关于
  onAbout() {
    wx.showModal({
      title: '关于清华食堂',
      content: '清华食堂 v1.0\n\n为清华同学打造的一站式食堂信息查询与评价平台。\n\n数据来源：同学贡献、饮食中心公开信息',
      showCancel: false,
    })
  },
})
