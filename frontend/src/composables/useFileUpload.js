/**
 * File upload composable for handling file validation and OCR processing.
 * 
 * @module composables/useFileUpload
 */

import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/axios'

/**
 * Composable for managing file upload operations.
 * 
 * @returns {Object} Object containing upload state and methods
 */
export function useFileUpload() {
  const uploadFile = ref(null)
  const fileList = ref([])
  const ocrResult = ref(null)
  const ocrFilename = ref('')

  /**
   * Validate uploaded file (extension, MIME type, and size).
   * 
   * @param {File} file - File object to validate
   * @returns {boolean} True if file is valid, false otherwise
   */
  const validateFile = (file) => {
    // Check file extension
    const fileName = file.name || ''
    const fileExtension = fileName.split('.').pop()?.toLowerCase()
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png']
    const isAllowedExtension = allowedExtensions.includes(fileExtension)
    
    // Check MIME type as secondary validation
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
    const isAllowedType = allowedTypes.includes(file.type)
    
    // Check file size
    const fileSizeMB = file.size / 1024 / 1024
    const maxSizeMB = 10
    const isLt10M = fileSizeMB < maxSizeMB

    // Validate file extension
    if (!isAllowedExtension) {
      ElMessage.error({
        message: `File type "${fileExtension || 'unknown'}" is not supported. Please upload a PDF, JPG, JPEG, or PNG file.`,
        duration: 5000,
        showClose: true
      })
      return false
    }
    
    // Validate MIME type (additional check)
    if (!isAllowedType) {
      ElMessage.error({
        message: 'Invalid file type detected. Please upload a PDF, JPG, JPEG, or PNG file.',
        duration: 5000,
        showClose: true
      })
      return false
    }
    
    // Validate file size
    if (!isLt10M) {
      ElMessage.error({
        message: `File size is ${fileSizeMB.toFixed(2)}MB, which exceeds the ${maxSizeMB}MB limit. Please upload a smaller file.`,
        duration: 5000,
        showClose: true
      })
      return false
    }
    
    return true
  }

  /**
   * Before upload hook for Element Plus upload component.
   * 
   * @param {File} file - File to validate
   * @returns {boolean} True if file is valid
   */
  const beforeUpload = (file) => {
    // Use the same validation function
    return validateFile(file)
  }

  /**
   * Handle file selection change.
   * 
   * @param {Object} file - File object from upload component
   */
  const handleFileChange = (file) => {
    // Validate file immediately when selected
    if (!validateFile(file.raw || file)) {
      // Remove invalid file from list
      uploadFile.value = null
      fileList.value = []
      return
    }
    
    uploadFile.value = file.raw || file
    fileList.value = [file]
  }

  /**
   * Handle file removal.
   */
  const handleRemove = () => {
    uploadFile.value = null
    fileList.value = []
  }

  /**
   * Process OCR on uploaded file.
   * 
   * @param {Function} [onSuccess] - Callback function called on success
   * @returns {Promise<boolean>} True if OCR processing succeeded
   */
  const processOCR = async (onSuccess) => {
    if (!uploadFile.value) {
      ElMessage.warning('Please upload a file first!')
      return false
    }

    try {
      const formData = new FormData()
      formData.append('file', uploadFile.value)

      const response = await api.post('/ocr', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const data = response.data

      // Backend returns: { message: "...", data: { extracted: ..., json_filename: ..., invoice_id: ..., ... } }
      if (data.data && data.data.extracted) {
        ocrResult.value = data.data
        ocrFilename.value = data.data.json_filename || ''
        
        ElMessage.success('Document processed successfully!')
        
        if (onSuccess) {
          // Pass invoice_id, file_created_at to callback
          onSuccess(data.data.extracted, data.data.file_created_at, data.data.invoice_id)
        }
        return true
      } else {
        console.error('Unexpected response format:', data)
        ElMessage.error({
          message: 'Unexpected response format from server. Please try again.',
          duration: 5000,
          showClose: true
        })
        return false
      }
    } catch (error) {
      console.error('OCR Error:', error)
      console.error('Error response:', error.response)
      console.error('Error status:', error.response?.status)
      console.error('Error data:', error.response?.data)
      
      // Handle different error types with friendly messages
      let errorMessage = 'Failed to process document'
      
      if (error.response) {
        const responseData = error.response.data
        const status = error.response.status
        
        // Helper function to check if error is related to file size
        const isFileSizeError = () => {
          const errorStr = (responseData?.error || '').toLowerCase()
          const messageStr = (responseData?.message || '').toLowerCase()
          return errorStr.includes('file') && (errorStr.includes('large') || errorStr.includes('size') || errorStr.includes('exceed')) ||
                 messageStr.includes('file') && (messageStr.includes('large') || messageStr.includes('size') || messageStr.includes('exceed'))
        }
        
        // Helper function to check if error is related to file type
        const isFileTypeError = () => {
          const errorStr = (responseData?.error || '').toLowerCase()
          const messageStr = (responseData?.message || '').toLowerCase()
          return errorStr.includes('type') || errorStr.includes('format') || 
                 messageStr.includes('type') || messageStr.includes('format') || 
                 messageStr.includes('not supported')
        }
        
        // Handle Veryfi API specific errors first
        if (responseData?.error === 'veryfi_auth_error') {
          errorMessage = responseData.message || 'Authentication credentials were not provided.'
        } else if (responseData?.error === 'veryfi_error') {
          errorMessage = responseData.message || "Couldn't download file from provided url."
        } else if (responseData?.error === 'rate_limit_error') {
          errorMessage = responseData.message || 'You have been rate limited. Please try again later.'
        } else if (responseData?.error === 'connection_error') {
          errorMessage = responseData.message || 'Client closed request or lost connection. Please try again.'
        } else if (responseData?.error === 'veryfi_server_error') {
          errorMessage = responseData.message || 'Unexpected error from OCR service. Please try again later.'
        } else if (responseData?.error === 'service_unavailable') {
          errorMessage = responseData.message || 'OCR service is temporarily unavailable. Please try again later.'
        }
        // Always check message if it exists (and not already handled above)
        else if (responseData?.message) {
          errorMessage = responseData.message
        }
        // Handle specific status codes
        else if (status === 413 || (status === 400 && (responseData?.error === 'file_too_large' || isFileSizeError()))) {
          // Handle file size errors (413 or 400 with file_too_large error)
          if (responseData?.error === 'File too large' || responseData?.error === 'file_too_large') {
            errorMessage = `File size exceeds the ${responseData.max_size_mb || 10}MB limit. Please upload a smaller file.`
          } else {
            errorMessage = 'File is too large. Maximum size is 10MB. Please upload a smaller file.'
          }
        } else if (status === 500 && (isFileSizeError() || isFileTypeError())) {
          // Check if 500 error is actually a file size or type error
          if (isFileSizeError()) {
            errorMessage = 'File is too large. Maximum size is 10MB. Please upload a smaller file.'
          } else if (isFileTypeError()) {
            errorMessage = 'Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG file.'
          }
        } else if (status === 400) {
          // Validation errors
          if (responseData?.error === 'validation_error') {
            errorMessage = 'Invalid file. Please check the file type and size.'
          } else if (responseData?.error === 'file_too_large') {
            errorMessage = 'File is too large. Maximum size is 10MB. Please upload a smaller file.'
          } else if (isFileTypeError()) {
            errorMessage = 'Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG file.'
          } else if (responseData?.error) {
            errorMessage = responseData.error
          }
        } else if (status === 415) {
          errorMessage = 'Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG file.'
        } else if (status === 500) {
          if (responseData?.error === 'configuration_error') {
            errorMessage = 'Server configuration error. Please contact support.'
          } else if (responseData?.error) {
            errorMessage = responseData.error
          } else {
            errorMessage = 'Server error occurred. Please try again later.'
          }
        } else if (status === 504) {
          errorMessage = 'Request timeout. The file may be too large or the server is busy. Please try again.'
        } else if (responseData?.error) {
          errorMessage = responseData.error
        }
      } else if (error.request) {
        errorMessage = 'Network error. Please check your internet connection and try again.'
      } else if (error.message) {
        // Only show raw error message if it's a known client-side error
        if (error.message.includes('Network') || error.message.includes('timeout')) {
          errorMessage = error.message
        }
      }
      
      ElMessage.error({
        message: errorMessage,
        duration: 6000,
        showClose: true
      })
      return false
    }
  }

  /**
   * Download OCR result JSON file.
   */
  const downloadJSON = async () => {
    if (!ocrFilename.value) {
      ElMessage.warning('No JSON file available')
      return
    }
    
    try {
      const response = await api.get(`/download-json/${ocrFilename.value}`, {
        responseType: 'blob'
      })
      
      const blob = response.data
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = ocrFilename.value
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('JSON file downloaded!')
    } catch (error) {
      console.error('Download error:', error)
      ElMessage.error('Failed to download file')
    }
  }

  return {
    uploadFile,
    fileList,
    ocrResult,
    ocrFilename,
    beforeUpload,
    handleFileChange,
    handleRemove,
    processOCR,
    downloadJSON
  }
}

