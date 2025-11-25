/**
 * XML operations composable for generating, validating, and downloading XML invoices.
 * 
 * @module composables/useXmlOperations
 */

import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/axios'

/**
 * Composable for managing XML operations.
 * 
 * @param {string} [initialXmlContent=''] - Initial XML content
 * @param {string} [initialXmlFilename=''] - Initial XML filename
 * @returns {Object} Object containing XML state and operations
 */
export function useXmlOperations(initialXmlContent = '', initialXmlFilename = '') {
  const xmlContent = ref(initialXmlContent)
  const xmlFilename = ref(initialXmlFilename)
  const validationResult = ref(null)
  const isValidating = ref(false)
  const currentInvoiceId = ref(null)

  /**
   * Generate XML from invoice data.
   * 
   * @param {Object} invoiceData - Invoice data object
   * @param {Function} [onSuccess] - Callback function called on success
   * @returns {Promise<boolean>} True if XML generation succeeded
   */
  const generateXML = async (invoiceData, onSuccess) => {
    try {
      // Extract invoice_id if present
      const invoiceId = invoiceData.invoice_id || null
      currentInvoiceId.value = invoiceId
      
      const response = await api.post('/generate-xml', invoiceData)
      const data = response.data

      // Backend returns { message, data: { xml_content, filename, invoice_id } }
      if (data && data.data) {
        xmlContent.value = data.data.xml_content
        xmlFilename.value = data.data.filename
        ElMessage.success('XML generated successfully!')
        
        // Auto-validate, pass invoice_id
        await validateXML(invoiceId)
        
        if (onSuccess) {
          onSuccess()
        }
        return true
      }
      ElMessage.error('Invalid response format from server')
      return false
    } catch (error) {
      console.error('XML Generation Error:', error)
      ElMessage.error(`Failed to generate XML: ${error.message}`)
      return false
    }
  }

  /**
   * Validate XML against AUNZ standards.
   * 
   * @param {number|null} [invoiceId=null] - Invoice ID for edit mode
   * @returns {Promise<boolean>} True if validation passed
   */
  const validateXML = async (invoiceId = null) => {
    if (!xmlContent.value) {
      ElMessage.warning('No XML content to validate')
      return false
    }

    isValidating.value = true
    
    try {
      const payload = {
          xml_content: xmlContent.value
      }
      
      // Add invoice_id if provided (for edit mode)
      if (invoiceId) {
        payload.invoice_id = invoiceId
      }
      
      const response = await api.post('/validate-xml', payload)

      const data = response.data
      
      // Backend validate-xml route returns jsonify(result) directly
      // Result structure: { success: bool, results: {...} }
      if (data && typeof data === 'object') {
      validationResult.value = data
      
        // Check if token was refreshed
      if (data.results && data.results.token_refreshed) {
        ElMessage.info({
          message: 'Authentication token was refreshed automatically and validation completed successfully.',
          duration: 5000,
          showClose: true
        })
      }
      
      if (data.success) {
        ElMessage.success('XML validation passed!')
        return true
      } else {
        ElMessage.warning('XML validation failed. Please check the errors.')
          return false
        }
      } else {
        // Fallback: handle unexpected structure
        console.warn('Unexpected validation response structure:', data)
        validationResult.value = { success: false, error: 'Invalid response format' }
        ElMessage.error('Invalid validation response format')
        return false
      }
      
    } catch (error) {
      console.error('Validation Error:', error)
      ElMessage.error(`Failed to validate XML: ${error.message}`)
      validationResult.value = { success: false, error: error.message }
      return false
    } finally {
      isValidating.value = false
    }
  }

  /**
   * Download XML file.
   */
  const downloadXML = () => {
    if (!xmlContent.value) {
      ElMessage.warning('No XML content available')
      return
    }
    
    try {
      const blob = new Blob([xmlContent.value], { type: 'application/xml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = xmlFilename.value || 'invoice.xml'
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('XML downloaded!')
    } catch (error) {
      console.error('Download error:', error)
      ElMessage.error('Failed to download XML file')
    }
  }

  return {
    xmlContent,
    xmlFilename,
    validationResult,
    isValidating,
    generateXML,
    validateXML,
    downloadXML
  }
}

