<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ color: stat.color }">
              <el-icon :size="36"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>最近更新</template>
          <el-timeline>
            <el-timeline-item
              v-for="(item, idx) in recentUpdates"
              :key="idx"
              :timestamp="item.time"
              :color="item.color"
            >
              {{ item.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>数据过期提醒</template>
          <el-empty v-if="staleItems.length === 0" description="暂无过期数据" />
          <el-table v-else :data="staleItems" size="small">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="type" label="类型" width="80" />
            <el-table-column prop="days" label="未更新(天)" width="100">
              <template #default="{ row }">
                <el-tag :type="row.days > 90 ? 'danger' : 'warning'">
                  {{ row.days }}天
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCanteens, getWindows, getDishes } from '../api'

const stats = ref([
  { label: '食堂', value: 0, icon: 'School', color: '#409EFF' },
  { label: '窗口', value: 0, icon: 'Grid', color: '#67C23A' },
  { label: '菜品', value: 0, icon: 'DishDot', color: '#E6A23C' },
  { label: '评价', value: 0, icon: 'ChatDotSquare', color: '#F56C6C' },
])

const recentUpdates = ref([])
const staleItems = ref([])

onMounted(async () => {
  try {
    const [canteens, windows, dishes] = await Promise.all([
      getCanteens({ page_size: 100 }),
      getWindows({ page_size: 100 }),
      getDishes({ page_size: 100 }),
    ])
    stats.value[0].value = canteens.total
    stats.value[1].value = windows.total
    stats.value[2].value = dishes.total
    stats.value[3].value = 0  // reviews count from API
  } catch (e) {
    console.error('Failed to load dashboard data', e)
  }
})
</script>

<style scoped>
.stat-card { cursor: pointer; }
.stat-content { display: flex; align-items: center; gap: 16px; }
.stat-icon { flex-shrink: 0; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 14px; color: #909399; margin-top: 4px; }
</style>
