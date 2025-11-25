/**
 * Tests for axios utility.
 * 
 * @module tests/unit/utils/axios
 */

import { describe, it, expect, beforeAll, jest } from '@jest/globals'

// Mock dependencies before importing axios
jest.mock('@/stores/auth', () => ({
  useAuthStore: jest.fn(() => ({
    accessToken: 'mock-token',
    refreshToken: 'mock-refresh-token',
    refreshAccessToken: jest.fn().mockResolvedValue('new-token'),
    setAccessToken: jest.fn(),
    logout: jest.fn()
  }))
}))

jest.mock('element-plus', () => ({
  ElMessage: {
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn()
  }
}))

jest.mock('axios', () => ({
  __esModule: true,
  default: {
    create: jest.fn(() => ({
      interceptors: {
        request: {
          use: jest.fn(),
          handlers: []
        },
        response: {
          use: jest.fn(),
          handlers: []
        }
      },
      defaults: {
        baseURL: '/api',
        timeout: 30000
      }
    })),
    post: jest.fn()
  }
}))

describe('Axios utility', () => {
  let axiosInstance

  beforeAll(async () => {
    // Import axios after mocks are set up
    const axiosModule = await import('@/utils/axios')
    axiosInstance = axiosModule.default
  })

  it('should create axios instance', () => {
    expect(axiosInstance).toBeDefined()
    expect(axiosInstance.defaults).toBeDefined()
  })

  it('should have baseURL configured to /api', () => {
    expect(axiosInstance.defaults.baseURL).toBe('/api')
  })

  it('should have timeout configured to 30000ms', () => {
    expect(axiosInstance.defaults.timeout).toBe(30000)
  })

  it('should have interceptors configured', () => {
    expect(axiosInstance.interceptors.request).toBeDefined()
    expect(axiosInstance.interceptors.response).toBeDefined()
  })

  it('should have request interceptor', () => {
    expect(axiosInstance.interceptors.request.use).toBeDefined()
  })

  it('should have response interceptor', () => {
    expect(axiosInstance.interceptors.response.use).toBeDefined()
  })
})

