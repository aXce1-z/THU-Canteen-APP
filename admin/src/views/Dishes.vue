<template>
  <div class="dishes-page">
    <el-card>
      <div class="toolbar">
        <h3>菜品管理</h3>
        <el-button type="primary" @click="showDialog()">
          <el-icon><Plus /></el-icon> 新增菜品
        </el-button>
      </div>

      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="6">
          <el-select v-model="filterWindowId" placeholder="筛选窗口" clearable @change="fetchData" filterable>
            <el-option v-for="w in windows" :key="w.id" :label="`${w.canteen_name} - ${w.name}`" :value="w.id" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterCategory" placeholder="筛选分类" clearable @change="fetchData">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-col>
      </el-row>

      <el-table :data="dishes" v-loading="loading" stripe>
        <el-table-column prop="name" label="菜名" width="150" />
        <el-table-column prop="window_name" label="所属窗口" width="120" />
        <el-table-column prop="canteen_name" label="食堂" width="100" />
        <el-table-column prop="category" label="分类" width="80" />
        <el-table-column label="价格" width="100">
          <template #default="{ row }">¥{{ row.price }}/{{ row.unit }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_available ? 'success' : 'info'">
              {{ row.is_available ? '供应中' : '已下架' }}
            </el-tag>
            <el-tag v-if="row.is_recommended" type="warning" size="small" style="margin-left: 4px">推荐</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avg_rating" label="评分" width="70" />
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

      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchData"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingDish ? '编辑菜品' : '新增菜品'"
      width="600px"
      @closed="resetForm"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属窗口" required>
          <el-select v-model="form.window_id" placeholder="选择窗口" filterable>
            <el-option v-for="w in windows" :key="w.id"
              :label="`${w.canteen_name} - ${w.name}`" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="菜品名称" required>
          <el-input v-model="form.name" placeholder="如：生煎包" @blur="autoMatchNutrition" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" placeholder="选择分类" clearable>
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="form.price" :min="0" :precision="2" :step="0.5" />
        </el-form-item>
        <el-form-item label="单位">
          <el-select v-model="form.unit">
            <el-option label="份" value="份" />
            <el-option label="碗" value="碗" />
            <el-option label="两" value="两" />
            <el-option label="个" value="个" />
            <el-option label="杯" value="杯" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_available" active-text="供应中" />
          <el-switch v-model="form.is_recommended" active-text="推荐" style="margin-left: 16px" />
        </el-form-item>
        <el-form-item label="营养成分">
          <el-row :gutter="10">
            <el-col :span="8"><el-input v-model="form.nutrition.calories" placeholder="热量(kcal)" size="small" /></el-col>
            <el-col :span="8"><el-input v-model="form.nutrition.protein" placeholder="蛋白质(g)" size="small" /></el-col>
            <el-col :span="8"><el-input v-model="form.nutrition.fat" placeholder="脂肪(g)" size="small" /></el-col>
          </el-row>
          <el-row :gutter="10" style="margin-top: 6px">
            <el-col :span="8"><el-input v-model="form.nutrition.carbs" placeholder="碳水(g)" size="small" /></el-col>
            <el-col :span="8"><el-input v-model="form.nutrition.fiber" placeholder="纤维(g)" size="small" /></el-col>
            <el-col :span="8"><el-input v-model="form.nutrition.sodium" placeholder="钠(mg)" size="small" /></el-col>
          </el-row>
          <div v-if="nutritionMatch" style="margin-top: 6px">
            <el-tag size="small" type="success" style="cursor: pointer" @click="applyNutrition(nutritionMatch)">
              自动匹配: {{ nutritionMatch.name }}
            </el-tag>
          </div>
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
import { getDishes, getWindows, createDish, updateDish, deleteDish, matchNutrition } from '../api'
import { ElMessage } from 'element-plus'

const dishes = ref([])
const windows = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterWindowId = ref(null)
const filterCategory = ref(null)

const categories = ['主食', '炒菜', '小吃', '汤粥', '饮品', '面食', '凉菜', '盖浇饭', '套餐', '麻辣烫', '其他']

const dialogVisible = ref(false)
const editingDish = ref(null)
const submitting = ref(false)
const nutritionMatch = ref(null)

const form = reactive({
  window_id: '',
  name: '',
  category: '',
  price: 0,
  unit: '份',
  is_available: true,
  is_recommended: false,
  nutrition: { calories: '', protein: '', fat: '', carbs: '', fiber: '', sodium: '' },
})

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterWindowId.value) params.window_id = filterWindowId.value
    if (filterCategory.value) params.category = filterCategory.value
    const [dishRes, winRes] = await Promise.all([
      getDishes(params),
      getWindows({ page_size: 100 }),
    ])
    dishes.value = dishRes.items
    total.value = dishRes.total
    windows.value = winRes.items
  } finally {
    loading.value = false
  }
}

async function autoMatchNutrition() {
  if (!form.name) return
  try {
    const res = await matchNutrition(form.name)
    const keys = Object.keys(res.matches || {})
    if (keys.length > 0) {
      nutritionMatch.value = { name: keys[0], data: res.matches[keys[0]] }
    }
  } catch { /* ignore */ }
}

function applyNutrition(match) {
  form.nutrition = {
    calories: match.data.calories || '',
    protein: match.data.protein || '',
    fat: match.data.fat || '',
    carbs: match.data.carbs || '',
    fiber: match.data.fiber || '',
    sodium: match.data.sodium || '',
  }
  nutritionMatch.value = null
  ElMessage.success(`已应用"${match.name}"的营养数据`)
}

function showDialog(dish) {
  if (dish) {
    editingDish.value = dish
    form.window_id = dish.window_id
    form.name = dish.name
    form.category = dish.category || ''
    form.price = dish.price
    form.unit = dish.unit || '份'
    form.is_available = dish.is_available
    form.is_recommended = dish.is_recommended
    form.nutrition = {
      calories: dish.nutrition?.calories || '',
      protein: dish.nutrition?.protein || '',
      fat: dish.nutrition?.fat || '',
      carbs: dish.nutrition?.carbs || '',
      fiber: dish.nutrition?.fiber || '',
      sodium: dish.nutrition?.sodium || '',
    }
  } else {
    editingDish.value = null
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  form.window_id = ''
  form.name = ''
  form.category = ''
  form.price = 0
  form.unit = '份'
  form.is_available = true
  form.is_recommended = false
  form.nutrition = { calories: '', protein: '', fat: '', carbs: '', fiber: '', sodium: '' }
  nutritionMatch.value = null
}

async function handleSubmit() {
  if (!form.window_id || !form.name) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    // Clean empty nutrition values
    const data = { ...form }
    for (const k of Object.keys(data.nutrition)) {
      if (data.nutrition[k] === '') data.nutrition[k] = null
      else data.nutrition[k] = Number(data.nutrition[k])
    }
    if (editingDish.value) {
      await updateDish(editingDish.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createDish(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  await deleteDish(id)
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
