/**
 * Tests for useFileUpload composable.
 * 
 * @module tests/unit/composables/useFileUpload
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals'
import { useFileUpload } from '@/composables/useFileUpload'

// Mock dependencies
jest.mock('@/utils/axios', () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
    get: jest.fn()
  }
}))

jest.mock('element-plus', () => ({
  ElMessage: {
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn()
  }
}))

describe('useFileUpload', () => {
  let upload
  let mockApi
  let mockElMessage

  beforeEach(() => {
    jest.clearAllMocks()
    upload = useFileUpload()
    
    const axiosModule = require('@/utils/axios')
    mockApi = axiosModule.default
    
    const elementPlusModule = require('element-plus')
    mockElMessage = elementPlusModule.ElMessage
  })

  describe('File validation', () => {
    it('should accept valid PDF file', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      Object.defineProperty(file, 'size', { value: 5 * 1024 * 1024 }) // 5MB
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(true)
    })

    it('should accept valid image file', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      Object.defineProperty(file, 'size', { value: 2 * 1024 * 1024 }) // 2MB
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(true)
    })

    it('should reject file with invalid extension', () => {
      const file = new File(['content'], 'test.txt', { type: 'text/plain' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalled()
    })

    it('should reject file exceeding size limit', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      Object.defineProperty(file, 'size', { value: 15 * 1024 * 1024 }) // 15MB
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalled()
    })

    it('should reject file with invalid MIME type', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/octet-stream' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(false)
    })
  })

  describe('File handling', () => {
    it('should handle file change', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      
      upload.handleFileChange({ raw: file })
      expect(upload.uploadFile.value).toBe(file)
      expect(upload.fileList.value.length).toBe(1)
    })

    it('should remove file', () => {
      upload.uploadFile.value = new File(['content'], 'test.pdf')
      upload.fileList.value = [{ name: 'test.pdf' }]
      
      upload.handleRemove()
      expect(upload.uploadFile.value).toBeNull()
      expect(upload.fileList.value.length).toBe(0)
    })
  })

  describe('OCR processing', () => {
    it('should process OCR successfully', async () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      upload.uploadFile.value = file

      const mockResponse = {
        data: {
          data: {
            extracted: { invoice_number: 'INV-001' },
            json_filename: 'result.json',
            invoice_id: 1,
            file_created_at: 1234567890
          }
        }
      }
      mockApi.post.mockResolvedValue(mockResponse)

      const onSuccess = jest.fn()
      const result = await upload.processOCR(onSuccess)

      expect(result).toBe(true)
      expect(mockApi.post).toHaveBeenCalledWith('/ocr', expect.any(FormData), expect.any(Object))
      expect(upload.ocrResult.value).toBeDefined()
      expect(onSuccess).toHaveBeenCalled()
      expect(mockElMessage.success).toHaveBeenCalled()
    })

    it('should handle OCR error when no file is uploaded', async () => {
      upload.uploadFile.value = null
      
      const result = await upload.processOCR()
      
      expect(result).toBe(false)
      expect(mockElMessage.warning).toHaveBeenCalledWith('Please upload a file first!')
    })

    it('should handle OCR API error', async () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      upload.uploadFile.value = file

      const mockError = {
        response: {
          status: 400,
          data: {
            error: 'validation_error',
            message: 'Invalid file type'
          }
        }
      }
      mockApi.post.mockRejectedValue(mockError)

      const result = await upload.processOCR()
      
      expect(result).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalled()
    })
  })

  describe('JSON download', () => {
    it('should download JSON file successfully', async () => {
      upload.ocrFilename.value = 'test.json'
      
      const mockBlob = new Blob(['{"test": "data"}'])
      const mockResponse = {
        data: mockBlob
      }
      mockApi.get.mockResolvedValue(mockResponse)

      // Mock URL and document methods
      global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = jest.fn()
      document.createElement = jest.fn(() => ({
        href: '',
        download: '',
        click: jest.fn()
      }))

      await upload.downloadJSON()

      expect(mockApi.get).toHaveBeenCalledWith('/download-json/test.json', {
        responseType: 'blob'
      })
      expect(mockElMessage.success).toHaveBeenCalled()
    })

    it('should warn when no JSON filename is available', async () => {
      upload.ocrFilename.value = ''
      
      await upload.downloadJSON()
      
      expect(mockElMessage.warning).toHaveBeenCalledWith('No JSON file available')
    })
  })
})

