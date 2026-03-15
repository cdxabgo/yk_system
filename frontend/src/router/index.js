import { createRouter, createWebHistory } from 'vue-router'
import Employee from '../views/Employee.vue'
import Disease from '../views/Disease.vue'
import HeartRate from '../views/HeartRate.vue'
import Duty from '../views/Duty.vue'

const routes = [
  { path: '/', redirect: '/employee' },
  { path: '/employee', component: Employee },
  { path: '/disease', component: Disease },
  { path: '/heartRate', component: HeartRate },
  { path: '/duty', component: Duty }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
