/**
 * Tests for useXmlOperations composable.
 * 
 * @module tests/unit/composables/useXmlOperations
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals'
import { useXmlOperations } from '@/composables/useXmlOperations'

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
    success: jest.fn(),
    info: jest.fn()
  }
}))

describe('useXmlOperations', () => {
  let xmlOps
  let mockApi
  let mockElMessage

  beforeEach(() => {
    jest.clearAllMocks()
    xmlOps = useXmlOperations()
    
    const axiosModule = require('@/utils/axios')
    mockApi = axiosModule.default
    
    const elementPlusModule = require('element-plus')
    mockElMessage = elementPlusModule.ElMessage
  })

  describe('Initial state', () => {
    it('should initialize with empty XML content', () => {
      expect(xmlOps.xmlContent.value).toBe('')
      expect(xmlOps.xmlFilename.value).toBe('')
      expect(xmlOps.validationResult.value).toBeNull()
      expect(xmlOps.isValidating.value).toBe(false)
    })

    it('should initialize with provided values', () => {
      const ops = useXmlOperations('<xml>test</xml>', 'test.xml')
      expect(ops.xmlContent.value).toBe('<xml>test</xml>')
      expect(ops.xmlFilename.value).toBe('test.xml')
    })
  })

  describe('XML generation', () => {
    it('should generate XML successfully', async () => {
      const invoiceData = {
        invoice_info: { invoice_number: 'INV-001' },
        supplier: { name: 'Test Supplier' },
        customer: { name: 'Test Customer' },
        line_items: [],
        summary: { subtotal: 100, tax_amount: 10, total: 110 }
      }

      const mockResponse = {
        data: {
          data: {
            xml_content: '<xml>generated</xml>',
            filename: 'invoice_123.xml',
            invoice_id: 1
          }
        }
      }
      mockApi.post.mockResolvedValueOnce(mockResponse) // For generate
      mockApi.post.mockResolvedValueOnce({ // For validate
        data: {
          success: true,
          results: {}
        }
      })

      const onSuccess = jest.fn()
      const result = await xmlOps.generateXML(invoiceData, onSuccess)

      expect(result).toBe(true)
      expect(xmlOps.xmlContent.value).toBe('<xml>generated</xml>')
      expect(xmlOps.xmlFilename.value).toBe('invoice_123.xml')
      expect(onSuccess).toHaveBeenCalled()
      expect(mockElMessage.success).toHaveBeenCalled()
    })

    it('should handle XML generation error', async () => {
      const invoiceData = { invoice_info: {} }
      mockApi.post.mockRejectedValue(new Error('Generation failed'))

      const result = await xmlOps.generateXML(invoiceData)

      expect(result).toBe(false)
      expect(mockElMessage.error).toHaveBeenCalled()
    })
  })

  describe('XML validation', () => {
    it('should validate XML successfully', async () => {
      xmlOps.xmlContent.value = '<xml>test</xml>'
      
      const mockResponse = {
        data: {
          success: true,
          results: {
            'AUNZ Invoice': { successful: true }
          }
        }
      }
      mockApi.post.mockResolvedValue(mockResponse)

      const result = await xmlOps.validateXML()

      expect(result).toBe(true)
      expect(xmlOps.validationResult.value.success).toBe(true)
      expect(xmlOps.isValidating.value).toBe(false)
      expect(mockElMessage.success).toHaveBeenCalled()
    })

    it('should handle validation failure', async () => {
      xmlOps.xmlContent.value = '<xml>invalid</xml>'
      
      const mockResponse = {
        data: {
          success: false,
          results: {
            'AUNZ Invoice': { 
              successful: false,
              message: 'Validation failed'
            }
          }
        }
      }
      mockApi.post.mockResolvedValue(mockResponse)

      const result = await xmlOps.validateXML()

      expect(result).toBe(false)
      expect(xmlOps.validationResult.value.success).toBe(false)
      expect(mockElMessage.warning).toHaveBeenCalled()
    })

    it('should warn when no XML content to validate', async () => {
      xmlOps.xmlContent.value = ''
      
      const result = await xmlOps.validateXML()

      expect(result).toBe(false)
      expect(mockElMessage.warning).toHaveBeenCalledWith('No XML content to validate')
    })

    it('should handle validation error', async () => {
      xmlOps.xmlContent.value = '<xml>test</xml>'
      mockApi.post.mockRejectedValue(new Error('Validation failed'))

      const result = await xmlOps.validateXML()

      expect(result).toBe(false)
      expect(xmlOps.validationResult.value.error).toBe('Validation failed')
      expect(mockElMessage.error).toHaveBeenCalled()
    })
  })

  describe('XML download', () => {
    it('should download XML file', () => {
      xmlOps.xmlContent.value = '<xml>content</xml>'
      xmlOps.xmlFilename.value = 'test.xml'

      // Mock URL and document methods
      global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = jest.fn()
      const mockAnchor = {
        href: '',
        download: '',
        click: jest.fn()
      }
      document.createElement = jest.fn(() => mockAnchor)

      xmlOps.downloadXML()

      expect(global.URL.createObjectURL).toHaveBeenCalled()
      expect(mockAnchor.download).toBe('test.xml')
      expect(mockAnchor.click).toHaveBeenCalled()
      expect(mockElMessage.success).toHaveBeenCalled()
    })

    it('should warn when no XML content available', () => {
      xmlOps.xmlContent.value = ''
      
      xmlOps.downloadXML()
      
      expect(mockElMessage.warning).toHaveBeenCalledWith('No XML content available')
    })

    it('should use default filename when filename is empty', () => {
      xmlOps.xmlContent.value = '<xml>content</xml>'
      xmlOps.xmlFilename.value = ''

      const mockAnchor = {
        href: '',
        download: '',
        click: jest.fn()
      }
      document.createElement = jest.fn(() => mockAnchor)
      global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = jest.fn()

      xmlOps.downloadXML()

      expect(mockAnchor.download).toBe('invoice.xml')
    })
  })
})





