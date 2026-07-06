const { createReview } = require('../../utils/api')

const COMMON_TAGS = ['分量足', '偏辣', '排队快', '性价比高', '口味好', '偏咸', '偏淡', '环境好', '速度快', '不推荐']

Page({
  data: {
    windowId: '',
    windowName: '',
    dishId: null,
    dishName: '',
    rating: 0,
    content: '',
    selectedTags: [],
    allTags: COMMON_TAGS,
    images: [],
    submitting: false,
  },

  onLoad(options) {
    this.setData({
      windowId: options.windowId || '',
      windowName: options.windowName || '',
      dishId: options.dishId || null,
      dishName: options.dishName || '',
    })
  },

  // 评分
  onRate(e) {
    this.setData({ rating: e.currentTarget.dataset.index })
  },

  // 输入内容
  onInput(e) {
    this.setData({ content: e.detail.value })
  },

  // 切换标签
  onToggleTag(e) {
    const tag = e.currentTarget.dataset.tag
    let tags = this.data.selectedTags
    const idx = tags.indexOf(tag)
    if (idx > -1) {
      tags.splice(idx, 1)
    } else {
      if (tags.length >= 5) {
        wx.showToast({ title: '最多选5个标签', icon: 'none' })
        return
      }
      tags.push(tag)
    }
    this.setData({ selectedTags: tags })
  },

  // 选择图片
  onChooseImage() {
    wx.chooseImage({
      count: 9 - this.data.images.length,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        // 实际项目中需要上传到OSS，这里先存临时路径
        const images = this.data.images.concat(res.tempFilePaths)
        this.setData({ images })
      },
    })
  },

  // 删除图片
  onRemoveImage(e) {
    const idx = e.currentTarget.dataset.index
    const images = this.data.images
    images.splice(idx, 1)
    this.setData({ images })
  },

  // 提交
  async onSubmit() {
    if (!this.data.rating) {
      wx.showToast({ title: '请先评分', icon: 'none' })
      return
    }

    this.setData({ submitting: true })
    try {
      const data = {
        rating: this.data.rating,
        content: this.data.content || '',
        tags: this.data.selectedTags,
        images: this.data.images,
      }
      if (this.data.dishId) {
        data.dish_id = this.data.dishId
      }

      await createReview(this.data.windowId, data)
      wx.showToast({ title: '评价成功！' })
      setTimeout(() => wx.navigateBack(), 1500)
    } catch (e) {
      console.error('评价失败', e)
    } finally {
      this.setData({ submitting: false })
    }
  },
})
