import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { noAuth: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
  },
  {
    path: '/canteens',
    name: 'Canteens',
    component: () => import('../views/Canteens.vue'),
  },
  {
    path: '/windows',
    name: 'Windows',
    component: () => import('../views/Windows.vue'),
  },
  {
    path: '/dishes',
    name: 'Dishes',
    component: () => import('../views/Dishes.vue'),
  },
  {
    path: '/reviews',
    name: 'Reviews',
    component: () => import('../views/Reviews.vue'),
  },
  {
    path: '/import',
    name: 'Import',
    component: () => import('../views/Import.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard
router.beforeEach((to, from, next) => {
  if (to.meta.noAuth) {
    return next()
  }
  const token = localStorage.getItem('admin_token')
  if (!token) {
    return next('/login')
  }
  next()
})

export default router
