<template>
  <div class="import-page">
    <el-card>
      <h3>批量导入菜品</h3>
      <p style="color: #909399; margin-bottom: 20px">
        上传 Excel 文件 (.xlsx) 批量导入菜品。Excel 格式：名称 | 分类 | 价格 | 单位 | 是否供应
      </p>

      <el-form label-width="120px">
        <el-form-item label="目标窗口" required>
          <el-select v-model="windowId" placeholder="选择窗口" filterable style="width: 400px">
            <el-option v-for="w in windows" :key="w.id"
              :label="`${w.canteen_name} - ${w.name}`" :value="w.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
            :on-remove="() => file = null"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon> 选择文件
            </el-button>
            <template #tip>
              <div style="margin-top: 8px">
                <el-button type="success" @click="downloadTemplate">
                  <el-icon><Download /></el-icon> 下载模板
                </el-button>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item v-if="file">
          <el-button type="primary" @click="handleImport" :loading="importing">
            <el-icon><Upload /></el-icon> 开始导入
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div v-if="previewData.length > 0">
        <h4>预览数据 (前10行)</h4>
        <el-table :data="previewData" size="small" border style="margin-top: 12px">
          <el-table-column prop="name" label="菜品名" />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="price" label="价格" width="80" />
          <el-table-column prop="unit" label="单位" width="80" />
          <el-table-column label="供应" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_available ? 'success' : 'info'" size="small">
                {{ row.is_available ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 校园卡消费导入 -->
    <el-card style="margin-top: 20px">
      <h3>校园卡消费导入</h3>
      <p style="color: #909399; margin-bottom: 16px">
        从 <a href="https://card.tsinghua.edu.cn/userselftrade" target="_blank">card.tsinghua.edu.cn</a> 导出交易记录 (CSV)，
        上传后自动分析各食堂消费统计和饮食日记。
      </p>

      <el-upload
        ref="cardUploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".csv,.xlsx,.xls"
        :on-change="handleCardFileChange"
        :on-remove="() => cardFile = null"
      >
        <el-button type="primary"><el-icon><Upload /></el-icon> 选择校园卡交易文件</el-button>
      </el-upload>

      <el-button v-if="cardFile" type="success" @click="handleCardImport" :loading="cardImporting" style="margin-top: 12px">
        开始分析
      </el-button>

      <el-divider v-if="cardResult" />

      <div v-if="cardResult">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="消费记录" :value="cardResult.total_records" suffix="条" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="总消费" :value="cardResult.total_spent" prefix="¥" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="覆盖天数" :value="cardResult.days_covered" suffix="天" />
          </el-col>
        </el-row>

        <h4 style="margin: 16px 0 8px">各食堂消费分布</h4>
        <el-table :data="cardResult.canteens" size="small" border>
          <el-table-column prop="name" label="食堂" />
          <el-table-column prop="count" label="次数" width="80" />
          <el-table-column label="金额" width="120">
            <template #default="{ row }">¥{{ row.amount }}</template>
          </el-table-column>
        </el-table>

        <h4 style="margin: 16px 0 8px">每日消费</h4>
        <el-table :data="cardResult.daily" size="small" border style="max-height: 300px; overflow-y: auto">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="count" label="次数" width="80" />
          <el-table-column label="金额" width="120">
            <template #default="{ row }">¥{{ row.amount }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getWindows, batchImportDishes } from '../api'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import * as XLSX from 'xlsx'

const windows = ref([])
const windowId = ref(null)
const file = ref(null)
const importing = ref(false)
const previewData = ref([])

async function fetchWindows() {
  const res = await getWindows({ page_size: 100 })
  windows.value = res.items
}

function handleFileChange(uploadFile) {
  file.value = uploadFile.raw
  // Generate preview
  const reader = new FileReader()
  reader.onload = (e) => {
    const data = new Uint8Array(e.target.result)
    const workbook = XLSX.read(data, { type: 'array' })
    const sheet = workbook.Sheets[workbook.SheetNames[0]]
    const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 })

    previewData.value = rows.slice(1, 11).map((row) => ({
      name: row[0] || '',
      category: row[1] || '',
      price: row[2] || 0,
      unit: row[3] || '份',
      is_available: row[4] !== false && row[4] !== '否',
    })).filter(r => r.name)
  }
  reader.readAsArrayBuffer(uploadFile.raw)
}

async function handleImport() {
  if (!windowId.value) {
    ElMessage.warning('请选择目标窗口')
    return
  }
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }
  importing.value = true
  try {
    const res = await batchImportDishes(windowId.value, file.value)
    ElMessage.success(res.message)
    previewData.value = []
    file.value = null
  } finally {
    importing.value = false
  }
}

function downloadTemplate() {
  const wb = XLSX.utils.book_new()
  const data = [
    ['菜品名称', '分类', '价格', '单位', '是否供应'],
    ['生煎包', '小吃', 3.5, '个', '是'],
    ['宫保鸡丁', '炒菜', 12, '份', '是'],
    ['番茄炒蛋', '炒菜', 6, '份', '否'],
  ]
  const ws = XLSX.utils.aoa_to_sheet(data)
  XLSX.utils.book_append_sheet(wb, ws, '菜品')
  XLSX.writeFile(wb, '菜品导入模板.xlsx')
}

// --- Card CSV import ---
const cardFile = ref(null)
const cardImporting = ref(false)
const cardResult = ref(null)
const cardUploadRef = ref(null)

function handleCardFileChange(uploadFile) {
  cardFile.value = uploadFile.raw
}

async function handleCardImport() {
  if (!cardFile.value) return
  cardImporting.value = true
  try {
    const formData = new FormData()
    formData.append('file', cardFile.value)
    const res = await axios.post('/api/diary/import', formData)
    cardResult.value = res.data
    ElMessage.success('分析完成')
  } catch (e) {
    // error shown by interceptor
  } finally {
    cardImporting.value = false
  }
}

onMounted(fetchWindows)
</script>
