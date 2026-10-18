import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '仪表盘', icon: 'Odometer' } },
      { path: 'departments', name: 'departments', component: () => import('@/views/Departments.vue'), meta: { title: '科室管理', icon: 'OfficeBuilding' } },
      { path: 'doctors', name: 'doctors', component: () => import('@/views/Doctors.vue'), meta: { title: '医生管理', icon: 'User' } },
      { path: 'exams', name: 'exams', component: () => import('@/views/Exams.vue'), meta: { title: '检查须知', icon: 'FirstAidKit' } },
      { path: 'medicines', name: 'medicines', component: () => import('@/views/Medicines.vue'), meta: { title: '用药常识', icon: 'TakeawayBox' } },
      { path: 'users', name: 'users', component: () => import('@/views/Users.vue'), meta: { title: '用户管理', icon: 'UserFilled' } },
      { path: 'navigation', name: 'navigation', component: () => import('@/views/Navigation.vue'), meta: { title: '院内导航', icon: 'MapLocation' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (to.path === '/login' && auth.isLoggedIn) return { path: '/dashboard' }
    return true
  }
  if (!auth.isLoggedIn) return { name: 'login' }
  return true
})

router.afterEach((to) => {
  const base = to.meta.title || '管理端'
  document.title = `${base} · 医院就医辅助管理端`
})

export default router
