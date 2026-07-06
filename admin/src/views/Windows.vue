<template>
  <div class="windows-page">
    <el-card>
      <div class="toolbar">
        <h3>窗口管理</h3>
        <el-button type="primary" @click="showDialog()">
          <el-icon><Plus /></el-icon> 新增窗口
        </el-button>
      </div>

      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="6">
          <el-select v-model="filterCanteenId" placeholder="筛选食堂" clearable @change="fetchData">
            <el-option v-for="c in canteens" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterPayment" placeholder="筛选支付方式" clearable @change="fetchData">
            <el-option label="校园卡" value="campus_card" />
            <el-option label="微信" value="wechat" />
            <el-option label="支付宝" value="alipay" />
          </el-select>
        </el-col>
      </el-row>

      <el-table :data="windows" v-loading="loading" stripe>
        <el-table-column prop="name" label="窗口名" width="150" />
        <el-table-column prop="canteen_name" label="所属食堂" width="120" />
        <el-table-column prop="window_number" label="编号" width="80" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column label="支付方式" width="180">
          <template #default="{ row }">
            <el-tag v-for="pm in row.payment_methods" :key="pm" size="small" style="margin: 2px"
              :type="pm === 'campus_card' ? '' : pm === 'wechat' ? 'success' : 'primary'">
              {{ payMethodLabel(pm) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avg_rating" label="评分" width="80" />
        <el-table-column prop="rating_count" label="评价数" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '营业中' : '已关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingWindow ? '编辑窗口' : '新增窗口'"
      width="600px"
      @closed="resetForm"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属食堂" required>
          <el-select v-model="form.canteen_id" placeholder="选择食堂">
            <el-option v-for="c in canteens" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="窗口名称" required>
          <el-input v-model="form.name" placeholder="如：川湘风味" />
        </el-form-item>
        <el-form-item label="窗口编号">
          <el-input v-model="form.window_number" placeholder="如：A12" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" placeholder="选择分类" clearable>
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="支付方式">
          <el-checkbox-group v-model="form.payment_methods">
            <el-checkbox label="campus_card">校园卡</el-checkbox>
            <el-checkbox label="wechat">微信</el-checkbox>
            <el-checkbox label="alipay">支付宝</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="营业状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { getWindows, getCanteens, createWindow, updateWindow, deleteWindow } from '../api'
import { ElMessage } from 'element-plus'

const windows = ref([])
const canteens = ref([])
const loading = ref(false)
const filterCanteenId = ref(null)
const filterPayment = ref(null)

const categories = ['自选餐', '盖浇饭', '面食', '小吃', '饮品', '套餐', '麻辣烫', '其他']

const dialogVisible = ref(false)
const editingWindow = ref(null)
const submitting = ref(false)

const form = reactive({
  canteen_id: '',
  name: '',
  window_number: '',
  category: '',
  payment_methods: ['campus_card'],
  is_active: true,
  description: '',
})

function payMethodLabel(pm) {
  const labels = { campus_card: '校园卡', wechat: '微信', alipay: '支付宝' }
  return labels[pm] || pm
}

async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (filterCanteenId.value) params.canteen_id = filterCanteenId.value
    if (filterPayment.value) params.payment_method = filterPayment.value
    const [winRes, canRes] = await Promise.all([
      getWindows({ ...params, page_size: 100 }),
      getCanteens({ page_size: 100 }),
    ])
    windows.value = winRes.items
    canteens.value = canRes.items
  } finally {
    loading.value = false
  }
}

function showDialog(win) {
  if (win) {
    editingWindow.value = win
    form.canteen_id = win.canteen_id
    form.name = win.name
    form.window_number = win.window_number || ''
    form.category = win.category || ''
    form.payment_methods = [...(win.payment_methods || ['campus_card'])]
    form.is_active = win.is_active
    form.description = win.description || ''
  } else {
    editingWindow.value = null
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  form.canteen_id = ''
  form.name = ''
  form.window_number = ''
  form.category = ''
  form.payment_methods = ['campus_card']
  form.is_active = true
  form.description = ''
}

async function handleSubmit() {
  if (!form.canteen_id || !form.name) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    const data = { ...form }
    if (editingWindow.value) {
      await updateWindow(editingWindow.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createWindow(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  await deleteWindow(id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
