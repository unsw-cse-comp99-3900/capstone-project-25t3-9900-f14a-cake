/**
 * Tests for useXmlUpload composable.
 * 
 * @module tests/unit/composables/useXmlUpload
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals'
import { useXmlUpload } from '@/composables/useXmlUpload'

// Mock dependencies
jest.mock('@/utils/axios', () => ({
  __esModule: true,
  default: {
    post: jest.fn()
  }
}))

jest.mock('element-plus', () => ({
  ElMessage: {
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn()
  }
}))

describe('useXmlUpload', () => {
  let upload
  let mockApi
  let mockElMessage

  beforeEach(() => {
    jest.clearAllMocks()
    upload = useXmlUpload()
    
    const axiosModule = require('@/utils/axios')
    mockApi = axiosModule.default
    
    const elementPlusModule = require('element-plus')
    mockElMessage = elementPlusModule.ElMessage
  })

  describe('File validation', () => {
    it('should accept valid XML file', () => {
      const file = new File(['<xml>content</xml>'], 'test.xml', { type: 'application/xml' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 }) // 1MB
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(true)
    })

    it('should reject non-XML file', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalledWith('Only XML files are supported!')
    })

    it('should reject file exceeding size limit', () => {
      const file = new File(['<xml>content</xml>'], 'test.xml', { type: 'application/xml' })
      Object.defineProperty(file, 'size', { value: 15 * 1024 * 1024 }) // 15MB
      
      const result = upload.beforeUpload(file)
      expect(result).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalled()
    })
  })

  describe('File handling', () => {
    it('should handle file change', () => {
      const file = new File(['<xml>content</xml>'], 'test.xml', { type: 'application/xml' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      
      upload.handleFileChange({ raw: file })
      expect(upload.uploadFile.value).toBe(file)
      expect(upload.fileList.value.length).toBe(1)
    })

    it('should remove file and clear XML content', () => {
      upload.uploadFile.value = new File(['<xml>content</xml>'], 'test.xml')
      upload.fileList.value = [{ name: 'test.xml' }]
      upload.xmlContent.value = '<xml>content</xml>'
      upload.xmlFilename.value = 'test.xml'
      
      upload.handleRemove()
      expect(upload.uploadFile.value).toBeNull()
      expect(upload.fileList.value.length).toBe(0)
      expect(upload.xmlContent.value).toBe('')
      expect(upload.xmlFilename.value).toBe('')
    })
  })

  describe('XML upload', () => {
    it('should upload XML file successfully', async () => {
      const file = new File(['<xml>content</xml>'], 'test.xml', { type: 'application/xml' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      upload.uploadFile.value = file

      const mockResponse = {
        data: {
          data: {
            xml_content: '<xml>uploaded</xml>',
            filename: 'uploaded_test.xml',
            file_created_at: 1234567890
          }
        }
      }
      mockApi.post.mockResolvedValue(mockResponse)

      const onSuccess = jest.fn()
      const result = await upload.uploadXmlFile(onSuccess)

      expect(result).toBe(true)
      expect(upload.xmlContent.value).toBe('<xml>uploaded</xml>')
      expect(upload.xmlFilename.value).toBe('uploaded_test.xml')
      expect(upload.fileCreatedAt.value).toBe(1234567890)
      expect(onSuccess).toHaveBeenCalled()
      expect(mockElMessage.success).toHaveBeenCalled()
    })

    it('should handle upload error when no file is uploaded', async () => {
      upload.uploadFile.value = null
      
      const result = await upload.uploadXmlFile()
      
      expect(result).toBe(false)
      expect(mockElMessage.warning).toHaveBeenCalledWith('Please upload an XML file first!')
    })

    it('should handle upload API error', async () => {
      const file = new File(['<xml>content</xml>'], 'test.xml', { type: 'application/xml' })
      Object.defineProperty(file, 'size', { value: 1 * 1024 * 1024 })
      upload.uploadFile.value = file

      const mockError = {
        response: {
          status: 400,
          data: {
            message: 'Invalid XML file'
          }
        }
      }
      mockApi.post.mockRejectedValue(mockError)

      const result = await upload.uploadXmlFile()
      
      expect(result).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalled()
    })
  })
})

