/**
 * Authentication store for managing user authentication state.
 * 
 * @module stores/auth
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import api from '@/utils/axios'

/**
 * Authentication store using Pinia.
 * 
 * Manages user authentication state, tokens, and authentication operations.
 * 
 * @returns {Object} Store object with state and actions
 */
export const useAuthStore = defineStore('auth', () => {
  // State
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Actions
  /**
   * Set access and refresh tokens.
   * 
   * @param {Object} tokens - Token object with access_token and refresh_token
   */
  const setTokens = (tokens) => {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  }

  /**
   * Set access token only.
   * 
   * @param {string} token - Access token string
   */
  const setAccessToken = (token) => {
    accessToken.value = token
    localStorage.setItem('access_token', token)
  }

  /**
   * Set user data.
   * 
   * @param {Object} userData - User object
   */
  const setUser = (userData) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  /**
   * Login user with email and password.
   * 
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Object with success status and user data or error
   */
  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', {
        email,
        password
      })

      if (response.data && response.data.data) {
        const { tokens, user: userData } = response.data.data
        
        setTokens(tokens)
        setUser(userData)
        
        ElMessage.success('Login successful')
        return { success: true, user: userData }
      }
      
      throw new Error('Invalid response format')
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Login failed'
      ElMessage.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  /**
   * Send email verification code.
   * 
   * @param {string} email - Email address
   * @returns {Promise<Object>} Object with success status
   */
  const sendVerificationCode = async (email) => {
    try {
      const response = await api.post('/auth/send-verification-code', {
        email
      })

      if (response.data) {
        ElMessage.success(response.data.message || 'Verification code sent successfully')
        return { success: true }
      }
      
      throw new Error('Invalid response format')
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to send verification code'
      ElMessage.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  /**
   * Register new user.
   * 
   * @param {string} username - Username
   * @param {string} email - Email address
   * @param {string} password - Password
   * @param {string} verificationCode - Email verification code
   * @returns {Promise<Object>} Object with success status and user data or error
   */
  const register = async (username, email, password, verificationCode) => {
    try {
      const response = await api.post('/auth/register', {
        username,
        email,
        password,
        verification_code: verificationCode
      })

      if (response.data && response.data.data) {
        const { tokens, user: userData } = response.data.data
        
        setTokens(tokens)
        setUser(userData)
        
        ElMessage.success('Registration successful')
        return { success: true, user: userData }
      }
      
      throw new Error('Invalid response format')
    } catch (error) {
      // Handle validation errors with detailed messages
      if (error.response?.data?.error === 'validation_error' && error.response?.data?.data?.errors) {
        const errors = error.response.data.data.errors
        // Extract and display validation errors
        const errorMessages = []
        if (errors.username) {
          errorMessages.push(...(Array.isArray(errors.username) ? errors.username : [errors.username]))
        }
        if (errors.email) {
          errorMessages.push(...(Array.isArray(errors.email) ? errors.email : [errors.email]))
        }
        if (errors.password) {
          errorMessages.push(...(Array.isArray(errors.password) ? errors.password : [errors.password]))
        }
        if (errors.verification_code) {
          errorMessages.push(...(Array.isArray(errors.verification_code) ? errors.verification_code : [errors.verification_code]))
        }
        
        const errorMessage = errorMessages.length > 0 
          ? errorMessages.join('; ') 
          : error.response?.data?.message || 'Validation failed'
        ElMessage.error(errorMessage)
        return { success: false, error: errorMessage }
      }
      
      // Handle other errors (email exists, username exists, etc.)
      const errorMessage = error.response?.data?.message || error.message || 'Registration failed'
      ElMessage.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  /**
   * Logout user and clear authentication state.
   */
  const logout = async () => {
    try {
      // Call logout endpoint if we have a token
      if (accessToken.value) {
        await api.post('/auth/logout')
      }
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error)
    } finally {
      // Clear local state
      accessToken.value = null
      refreshToken.value = null
      user.value = null
      
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      
      // Redirect to login
      router.push('/login')
    }
  }

  /**
   * Refresh access token using refresh token.
   * 
   * @returns {Promise<string>} New access token
   * @throws {Error} If refresh fails
   */
  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await axios.post('/api/auth/refresh', {}, {
        headers: {
          Authorization: `Bearer ${refreshToken.value}`
        }
      })

      if (response.data && response.data.data) {
        const { access_token } = response.data.data
        setAccessToken(access_token)
        return access_token
      }
      
      throw new Error('Invalid response format')
    } catch (error) {
      // Refresh failed, logout user
      logout()
      throw error
    }
  }

  /**
   * Fetch current user profile.
   * 
   * @returns {Promise<Object>} User object
   * @throws {Error} If fetch fails
   */
  const fetchProfile = async () => {
    try {
      const response = await api.get('/auth/profile')

      if (response.data && response.data.data) {
        const userData = response.data.data.user
        setUser(userData)
        return userData
      }
      
      throw new Error('Invalid response format')
    } catch (error) {
      console.error('Failed to fetch profile:', error)
      throw error
    }
  }

  /**
   * Update user profile.
   * 
   * @param {Object} profileData - Profile data to update
   * @returns {Promise<Object>} Updated user object
   * @throws {Error} If update fails
   */
  const updateProfile = async (profileData) => {
    try {
      const response = await api.put('/auth/profile', profileData)

      if (response.data && response.data.data) {
        const userData = response.data.data.user
        setUser(userData)
        ElMessage.success('Profile updated successfully')
        return userData
      }
      
      throw new Error('Invalid response format')
    } catch (error) {
      // Handle validation errors with detailed messages
      if (error.response?.data?.error === 'validation_error' && error.response?.data?.data?.errors) {
        const errors = error.response.data.data.errors
        // Extract and display validation errors
        const errorMessages = []
        if (errors.username) {
          errorMessages.push(...(Array.isArray(errors.username) ? errors.username : [errors.username]))
        }
        if (errors.email) {
          errorMessages.push(...(Array.isArray(errors.email) ? errors.email : [errors.email]))
        }
        if (errors.password) {
          errorMessages.push(...(Array.isArray(errors.password) ? errors.password : [errors.password]))
        }
        if (errors.verification_code) {
          errorMessages.push(...(Array.isArray(errors.verification_code) ? errors.verification_code : [errors.verification_code]))
        }
        
        const errorMessage = errorMessages.length > 0 
          ? errorMessages.join('; ') 
          : error.response?.data?.message || 'Validation failed'
        ElMessage.error(errorMessage)
        throw new Error(errorMessage)
      }
      
      // Handle other errors (username exists, email exists, etc.)
      const errorMessage = error.response?.data?.message || error.message || 'Failed to update profile'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  /**
   * Reset password using email verification code.
   * 
   * @param {string} email - Email address
   * @param {string} verificationCode - Verification code
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} Object with success status
   */
  const resetPassword = async (email, verificationCode, newPassword) => {
    try {
      const response = await api.post('/auth/reset-password', {
        email,
        verification_code: verificationCode,
        password: newPassword
      })

      if (response.data) {
        ElMessage.success(response.data.message || 'Password reset successfully')
        return { success: true }
      }
      
      throw new Error('Invalid response format')
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to reset password'
      ElMessage.error(errorMessage)
      return { success: false, error: errorMessage }
    }
  }

  /**
   * Initialize store: Check if user is logged in on app start.
   * Verifies token validity by fetching profile.
   */
  const init = async () => {
    if (accessToken.value && user.value) {
      // Verify token is still valid by fetching profile
      try {
        await fetchProfile()
      } catch (error) {
        // Token invalid, clear auth state
        logout()
      }
    }
  }

  return {
    // State
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    isAdmin,
    
    // Actions
    login,
    register,
    sendVerificationCode,
    resetPassword,
    logout,
    refreshAccessToken,
    fetchProfile,
    updateProfile,
    setTokens,
    setAccessToken,
    setUser,
    init
  }
})

