import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../pages/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../pages/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/scanner',
    name: 'Scanner',
    component: () => import('../pages/Scanner.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/token/:pairId',
    name: 'TokenDetail',
    component: () => import('../pages/TokenDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/positions',
    name: 'Positions',
    component: () => import('../pages/Positions.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../pages/Settings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/audit',
    name: 'Audit',
    component: () => import('../pages/Audit.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/watchlist-history',
    name: 'WatchlistHistory',
    component: () => import('../pages/WatchlistHistory.vue'),
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  authStore.loadToken()
  
  const requiresAuth = to.meta.requiresAuth
  const isAuthenticated = authStore.isAuthenticated

  if (requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (!requiresAuth && isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    next('/')
  } else {
    next()
  }
})

export default router
