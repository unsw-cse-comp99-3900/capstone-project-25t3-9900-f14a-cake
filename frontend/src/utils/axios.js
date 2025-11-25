/**
 * Axios HTTP client configuration with JWT authentication and error handling.
 * 
 * This module exports a configured axios instance with:
 * - Request interceptor: Automatically adds JWT token to requests
 * - Response interceptor: Handles token refresh and error responses
 * 
 * @module utils/axios
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

/**
 * Configured axios instance for API requests.
 * 
 * Base URL: '/api'
 * Timeout: 30 seconds
 * 
 * @type {import('axios').AxiosInstance}
 */
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * Request interceptor: Adds JWT token to all outgoing requests.
 * 
 * Automatically retrieves the access token from the auth store and
 * adds it to the Authorization header if available.
 */
api.interceptors.request.use(
  /**
   * @param {import('axios').InternalAxiosRequestConfig} config - Request configuration
   * @returns {import('axios').InternalAxiosRequestConfig} Modified request configuration
   */
  (config) => {
    const authStore = useAuthStore()
    
    // Add access token to request headers if available
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    
    return config
  },
  /**
   * @param {Error} error - Request error
   * @returns {Promise<never>} Rejected promise with error
   */
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor: Handles token refresh and error responses.
 * 
 * - Automatically refreshes access token on 401 errors
 * - Logs out user if token refresh fails
 * - Handles network errors and displays appropriate messages
 */
api.interceptors.response.use(
  /**
   * @param {import('axios').AxiosResponse} response - Successful response
   * @returns {import('axios').AxiosResponse} Response object
   */
  (response) => {
    return response
  },
  /**
   * @param {import('axios').AxiosError} error - Error object
   * @returns {Promise<import('axios').AxiosResponse>|Promise<never>} Response or rejected promise
   */
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config

    // Handle 401 Unauthorized - Token expired or invalid
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // If we have a refresh token, try to refresh the access token
      if (authStore.refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', {}, {
            headers: {
              Authorization: `Bearer ${authStore.refreshToken}`
            }
          })

          const { access_token } = response.data.data
          
          // Update access token in store
          authStore.setAccessToken(access_token)
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, logout user
          authStore.logout()
          
          // Redirect to login if not already there
          if (window.location.pathname !== '/login') {
            ElMessage.error('Session expired. Please login again.')
            window.location.href = '/login'
          }
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token, logout and redirect
        authStore.logout()
        if (window.location.pathname !== '/login') {
          ElMessage.error('Please login to continue')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    }

    // Handle other errors
    if (error.response) {
      const { data } = error.response
      const status = error.response.status
      
      // Don't show error message for 401 (already handled above)
      // Also don't show error for 413 (file too large), 400 (validation errors), and 500 (server errors)
      // Let the specific component handle these with better context
      // 500 errors might be file size related, so let components handle them
      if (status !== 401 && status !== 413 && status !== 400 && status !== 500) {
        const errorMessage = data?.message || data?.error || 'An error occurred'
        ElMessage.error(errorMessage)
      }
    } else if (error.request) {
      ElMessage.error('Network error. Please check your connection.')
    } else {
      ElMessage.error('An unexpected error occurred')
    }

    return Promise.reject(error)
  }
)

export default api

