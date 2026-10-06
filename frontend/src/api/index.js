/**
 * Module cấu hình Axios client và xuất các hàm gọi API REST tới Backend (auth, tickets, reports).
 */

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

/** API client cho xác thực tài khoản */
export const authApi = {
  login: (credentials) => api.post('/auth/login/', credentials),
  register: (userData) => api.post('/auth/register/', userData),
  logout: () => api.post('/auth/logout/'),
  me: () => api.get('/auth/me/'),
};

/** API client cho quản lý vé xe, xe vào/ra và vé tháng */
export const ticketsApi = {
  checkIn: (data) => api.post('/tickets/check-in/', data),
  checkOut: (data) => api.post('/tickets/check-out/', data),
  getInLot: () => api.get('/tickets/in-lot/'),
  getHistory: (params) => api.get('/tickets/history/', { params }),
  getMonthly: (params) => api.get('/tickets/monthly/', { params }),
  addMonthly: (data) => api.post('/tickets/monthly/', data),
};

/** API client cho thống kê, báo cáo và xuất Excel */
export const reportsApi = {
  getSummary: () => api.get('/reports/summary/'),
  getCharts: () => api.get('/reports/charts/'),
  exportExcel: (type = 'all') => `/api/reports/export/excel/?type=${type}`,
};

export default api;

