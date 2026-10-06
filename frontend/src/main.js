/**
 * Điểm khởi chạy (Entry point) của ứng dụng Frontend Vue 3.
 */

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')
