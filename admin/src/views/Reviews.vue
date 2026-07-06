<template>
  <div class="reviews-page">
    <el-card>
      <h3>评价管理</h3>
      <p style="color: #909399; margin-bottom: 16px">审核和管理用户评价</p>

      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :span="6">
          <el-select v-model="filterWindowId" placeholder="筛选窗口" clearable filterable @change="fetchData">
            <el-option v-for="w in windows" :key="w.id" :label="`${w.canteen_name} - ${w.name}`" :value="w.id" />
          </el-select>
        </el-col>
      </el-row>

      <el-table :data="reviews" v-loading="loading" stripe>
        <el-table-column prop="user_nickname" label="用户" width="100" />
        <el-table-column label="评分" width="180">
          <template #default="{ row }">
            <el-rate v-model="row.rating" disabled show-score size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="250" show-overflow-tooltip />
        <el-table-column label="标签" width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin: 2px">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="like_count" label="点赞" width="80" />
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleDateString() }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-popconfirm title="确定删除该评价？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getWindows, getWindowReviews } from '../api'

const reviews = ref([])
const windows = ref([])
const loading = ref(false)
const filterWindowId = ref(null)

async function fetchData() {
  loading.value = true
  try {
    const winRes = await getWindows({ page_size: 100 })
    windows.value = winRes.items

    if (filterWindowId.value) {
      const revRes = await getWindowReviews(filterWindowId.value, { page_size: 100 })
      reviews.value = revRes.items
    } else {
      // Load reviews from first few windows
      reviews.value = []
      for (const w of winRes.items.slice(0, 5)) {
        try {
          const revRes = await getWindowReviews(w.id, { page_size: 10 })
          reviews.value.push(...revRes.items)
        } catch { /* skip */ }
      }
    }
  } finally {
    loading.value = false
  }
}

async function handleDelete(id) {
  // Review delete would need admin API
  reviews.value = reviews.value.filter(r => r.id !== id)
}

onMounted(fetchData)
</script>
