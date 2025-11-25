/**
 * Tests for auth store.
 * 
 * @module tests/unit/stores/auth
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

// Mock dependencies
jest.mock('@/utils/axios', () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
    get: jest.fn(),
    put: jest.fn()
  }
}))

jest.mock('@/router', () => ({
  __esModule: true,
  default: {
    push: jest.fn()
  }
}))

jest.mock('element-plus', () => ({
  ElMessage: {
    error: jest.fn(),
    success: jest.fn()
  }
}))

jest.mock('axios', () => ({
  __esModule: true,
  default: {
    post: jest.fn()
  }
}))

describe('useAuthStore', () => {
  let store
  let mockApi
  let mockRouter
  let mockElMessage

  beforeEach(() => {
    // Clear localStorage
    localStorage.clear()
    
    // Reset Pinia
    setActivePinia(createPinia())
    
    // Clear all mocks
    jest.clearAllMocks()
    
    // Get store instance
    store = useAuthStore()
    
    // Get mocked modules
    const axiosModule = require('@/utils/axios')
    mockApi = axiosModule.default
    
    const routerModule = require('@/router')
    mockRouter = routerModule.default
    
    const elementPlusModule = require('element-plus')
    mockElMessage = elementPlusModule.ElMessage
  })

  describe('Initial state', () => {
    it('should initialize with null tokens when no localStorage data', () => {
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.user).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isAdmin).toBe(false)
    })

  })

  describe('Token management', () => {
    it('should set tokens', () => {
      const tokens = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token'
      }
      
      store.setTokens(tokens)
      
      expect(store.accessToken).toBe('new-access-token')
      expect(store.refreshToken).toBe('new-refresh-token')
      expect(localStorage.getItem('access_token')).toBe('new-access-token')
      expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')
    })

    it('should set access token only', () => {
      store.setAccessToken('new-token')
      
      expect(store.accessToken).toBe('new-token')
      expect(localStorage.getItem('access_token')).toBe('new-token')
    })

    it('should set user data', () => {
      const userData = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      }
      
      store.setUser(userData)
      
      expect(store.user).toEqual(userData)
      expect(JSON.parse(localStorage.getItem('user'))).toEqual(userData)
    })
  })

  describe('Authentication status', () => {
    it('should be authenticated when token and user exist', () => {
      store.setAccessToken('token')
      store.setUser({ id: 1, username: 'test' })
      
      expect(store.isAuthenticated).toBe(true)
    })

    it('should not be authenticated when token is missing', () => {
      store.setUser({ id: 1, username: 'test' })
      
      expect(store.isAuthenticated).toBe(false)
    })

    it('should identify admin user', () => {
      store.setUser({ id: 1, username: 'admin', role: 'admin' })
      
      expect(store.isAdmin).toBe(true)
    })

    it('should not identify regular user as admin', () => {
      store.setUser({ id: 1, username: 'user', role: 'user' })
      
      expect(store.isAdmin).toBe(false)
    })
  })

  describe('Login', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            tokens: {
              access_token: 'access-token',
              refresh_token: 'refresh-token'
            },
            user: {
              id: 1,
              username: 'testuser',
              email: 'test@example.com',
              role: 'user'
            }
          }
        }
      }
      mockApi.post.mockResolvedValue(mockResponse)

      const result = await store.login('test@example.com', 'password123')

      expect(result.success).toBe(true)
      expect(store.accessToken).toBe('access-token')
      expect(store.user.username).toBe('testuser')
      expect(mockElMessage.success).toHaveBeenCalledWith('Login successful')
    })

    it('should handle login error', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Invalid credentials'
          }
        }
      }
      mockApi.post.mockRejectedValue(mockError)

      const result = await store.login('test@example.com', 'wrongpassword')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid credentials')
      expect(mockElMessage.error).toHaveBeenCalled()
    })
  })

  describe('Registration', () => {
    it('should register successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            tokens: {
              access_token: 'access-token',
              refresh_token: 'refresh-token'
            },
            user: {
              id: 1,
              username: 'newuser',
              email: 'new@example.com',
              role: 'user'
            }
          }
        }
      }
      mockApi.post.mockResolvedValue(mockResponse)

      const result = await store.register('newuser', 'new@example.com', 'password123', '123456')

      expect(result.success).toBe(true)
      expect(store.user.username).toBe('newuser')
      expect(mockElMessage.success).toHaveBeenCalledWith('Registration successful')
    })

    it('should handle registration error', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Email already exists'
          }
        }
      }
      mockApi.post.mockRejectedValue(mockError)

      const result = await store.register('user', 'test@example.com', 'pass', '123456')

      expect(result.success).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalled()
    })
  })

  describe('Logout', () => {
    it('should logout and clear state', async () => {
      store.setTokens({
        access_token: 'token',
        refresh_token: 'refresh-token'
      })
      store.setUser({ id: 1, username: 'test' })
      
      mockApi.post.mockResolvedValue({})

      await store.logout()

      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.user).toBeNull()
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(mockRouter.push).toHaveBeenCalledWith('/login')
    })

    it('should logout even if API call fails', async () => {
      store.setAccessToken('token')
      mockApi.post.mockRejectedValue(new Error('API error'))

      await store.logout()

      expect(store.accessToken).toBeNull()
      expect(mockRouter.push).toHaveBeenCalledWith('/login')
    })
  })

  describe('Token refresh', () => {
    it('should refresh access token successfully', async () => {
      store.setTokens({
        access_token: 'token',
        refresh_token: 'refresh-token'
      })
      
      const axios = require('axios')
      const mockResponse = {
        data: {
          data: {
            access_token: 'new-access-token'
          }
        }
      }
      axios.default.post.mockResolvedValue(mockResponse)

      const newToken = await store.refreshAccessToken()

      expect(newToken).toBe('new-access-token')
      expect(store.accessToken).toBe('new-access-token')
    })

    it('should throw error when no refresh token available', async () => {
      // Clear tokens
      store.setTokens({
        access_token: null,
        refresh_token: null
      })

      await expect(store.refreshAccessToken()).rejects.toThrow('No refresh token available')
    })

  })

  describe('Profile management', () => {
    it('should fetch profile successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            user: {
              id: 1,
              username: 'testuser',
              email: 'test@example.com'
            }
          }
        }
      }
      mockApi.get.mockResolvedValue(mockResponse)

      const user = await store.fetchProfile()

      expect(user.username).toBe('testuser')
      expect(store.user.username).toBe('testuser')
    })

    it('should update profile successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            user: {
              id: 1,
              username: 'updateduser',
              email: 'updated@example.com'
            }
          }
        }
      }
      mockApi.put.mockResolvedValue(mockResponse)

      const user = await store.updateProfile({ username: 'updateduser' })

      expect(user.username).toBe('updateduser')
      expect(store.user.username).toBe('updateduser')
      expect(mockElMessage.success).toHaveBeenCalled()
    })
  })
})

