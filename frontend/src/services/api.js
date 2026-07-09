import axios from 'axios'
import { API_BASE_URL, TOKEN_KEYS } from '../utils/constants'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,  // Send cookies (for CSRF state cookie in OAuth)
})

// Request interceptor — attach JWT Bearer token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEYS.ACCESS)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle 401 with automatic token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Only attempt refresh on 401 from non-auth endpoints (avoid infinite loops)
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register')
    ) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem(TOKEN_KEYS.REFRESH)

      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem(TOKEN_KEYS.ACCESS, data.access_token)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed — clear everything and redirect
          localStorage.removeItem(TOKEN_KEYS.ACCESS)
          localStorage.removeItem(TOKEN_KEYS.REFRESH)
          localStorage.removeItem('user')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token available — just clear and redirect
        localStorage.removeItem(TOKEN_KEYS.ACCESS)
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
