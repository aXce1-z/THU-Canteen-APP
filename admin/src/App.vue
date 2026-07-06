<template>
  <!-- Login page: no sidebar/header -->
  <router-view v-if="$route.meta.noAuth" />

  <el-container v-else class="admin-layout">
    <el-aside width="220px">
      <div class="logo">
        <h2>🍽️ 清华食堂管理</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/canteens">
          <el-icon><School /></el-icon>
          <span>食堂管理</span>
        </el-menu-item>
        <el-menu-item index="/windows">
          <el-icon><Grid /></el-icon>
          <span>窗口管理</span>
        </el-menu-item>
        <el-menu-item index="/dishes">
          <el-icon><DishDot /></el-icon>
          <span>菜品管理</span>
        </el-menu-item>
        <el-menu-item index="/reviews">
          <el-icon><ChatDotSquare /></el-icon>
          <span>评价审核</span>
        </el-menu-item>
        <el-menu-item index="/import">
          <el-icon><Upload /></el-icon>
          <span>批量导入</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <span class="title">{{ pageTitle }}</span>
        <div style="margin-left: auto; display: flex; align-items: center; gap: 12px">
          <span style="color: #666; font-size: 13px">{{ userName }}</span>
          <el-button size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)

const userName = computed(() => {
  const user = JSON.parse(localStorage.getItem('admin_user') || 'null')
  return user?.nickname || ''
})

const pageTitle = computed(() => {
  const titles = {
    '/': '仪表盘',
    '/canteens': '食堂管理',
    '/windows': '窗口管理',
    '/dishes': '菜品管理',
    '/reviews': '评价审核',
    '/import': '批量导入',
  }
  return titles[route.path] || '清华食堂管理后台'
})

function handleLogout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_user')
  router.push('/login')
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

.admin-layout {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  overflow-y: auto;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #4a5568;
}

.logo h2 {
  color: #fff;
  font-size: 18px;
}

.el-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
}

.el-header .title {
  font-size: 18px;
  font-weight: 600;
}

.el-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>
