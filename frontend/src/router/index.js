import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Employee from '../views/Employee.vue'
import Disease from '../views/Disease.vue'
import HeartRate from '../views/HeartRate.vue'
import Monitor from '../views/Monitor.vue'
import RealtimeMonitor from '../views/RealtimeMonitor.vue'
import Dashboard from '../views/Dashboard.vue'
import EmployeeDetail from '../views/EmployeeDetail.vue'
import HealthAdvice from '../views/HealthAdvice.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/', redirect: '/employee' },
  { path: '/employee', component: Employee, meta: { requiresAuth: true } },
  { path: '/disease', component: Disease, meta: { requiresAuth: true } },
  { path: '/heartRate', component: HeartRate, meta: { requiresAuth: true } },
  { path: '/monitor', component: Monitor, meta: { requiresAuth: true } },
  { path: '/realtime', component: RealtimeMonitor, meta: { requiresAuth: true } },
  { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/healthAdvice', component: HealthAdvice, meta: { requiresAuth: true } },
  { path: '/employee-detail/:id', component: EmployeeDetail, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/employee')
  } else {
    next()
  }
})

export default router
