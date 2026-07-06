<template>
  <div class="canteens-page">
    <el-card>
      <div class="toolbar">
        <h3>食堂列表</h3>
        <el-button type="primary" @click="showDialog()">
          <el-icon><Plus /></el-icon> 新增食堂
        </el-button>
      </div>

      <el-table :data="canteens" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="location" label="位置" min-width="200" />
        <el-table-column prop="window_count" label="窗口数" width="80" align="center" />
        <el-table-column label="营业时间" width="220">
          <template #default="{ row }">
            <template v-if="row.opening_hours">
              <el-tag v-for="(v, k) in row.opening_hours" :key="k" size="small" style="margin: 2px">
                {{ k }}: {{ v }}
              </el-tag>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除该食堂？删除后窗口和菜品也将被删除" @confirm="handleDelete(row.id)">
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
      :title="editingCanteen ? '编辑食堂' : '新增食堂'"
      width="600px"
      @closed="resetForm"
    >
      <el-form :model="form" label-width="100px" ref="formRef">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如：紫荆园" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="如：紫荆学生公寓区" />
        </el-form-item>
        <el-form-item label="图片URL">
          <el-input v-model="form.image_url" placeholder="食堂封面图链接" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="营业时间">
          <div v-for="(v, k, idx) in form.opening_hours" :key="idx" style="display: flex; gap: 8px; margin-bottom: 8px">
            <el-input v-model="form.opening_hours[k]" :placeholder="k" style="flex: 1" disabled />
            <el-button @click="deleteOpeningHour(k)" type="danger" size="small">删除</el-button>
          </div>
          <div style="display: flex; gap: 8px">
            <el-input v-model="newHourKey" placeholder="如: 早餐" size="small" style="width: 120px" />
            <el-input v-model="newHourVal" placeholder="如: 6:30-9:00" size="small" style="flex: 1" />
            <el-button @click="addOpeningHour" size="small">添加</el-button>
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
import { getCanteens, createCanteen, updateCanteen, deleteCanteen } from '../api'
import { ElMessage } from 'element-plus'

const canteens = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const editingCanteen = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const newHourKey = ref('')
const newHourVal = ref('')

const form = reactive({
  name: '',
  location: '',
  image_url: '',
  description: '',
  opening_hours: {},
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getCanteens({ page: page.value, page_size: pageSize.value })
    canteens.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function showDialog(canteen) {
  if (canteen) {
    editingCanteen.value = canteen
    form.name = canteen.name
    form.location = canteen.location || ''
    form.image_url = canteen.image_url || ''
    form.description = canteen.description || ''
    form.opening_hours = canteen.opening_hours ? { ...canteen.opening_hours } : {}
  } else {
    editingCanteen.value = null
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  form.name = ''
  form.location = ''
  form.image_url = ''
  form.description = ''
  form.opening_hours = {}
  newHourKey.value = ''
  newHourVal.value = ''
}

function addOpeningHour() {
  if (newHourKey.value && newHourVal.value) {
    form.opening_hours[newHourKey.value] = newHourVal.value
    newHourKey.value = ''
    newHourVal.value = ''
  }
}

function deleteOpeningHour(key) {
  delete form.opening_hours[key]
}

async function handleSubmit() {
  if (!form.name) {
    ElMessage.warning('请输入食堂名称')
    return
  }
  submitting.value = true
  try {
    const data = { ...form }
    if (editingCanteen.value) {
      await updateCanteen(editingCanteen.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createCanteen(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  await deleteCanteen(id)
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
