/**
 * Cấu hình Vue Router định tuyến các trang ứng dụng SPA Frontend.
 */

import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    }
  ]
})

export default router
