/**
 * XML upload composable for handling XML file uploads.
 * 
 * @module composables/useXmlUpload
 */

import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/axios'

/**
 * Composable for managing XML file upload operations.
 * 
 * @returns {Object} Object containing upload state and methods
 */
export function useXmlUpload() {
  const uploadFile = ref(null)
  const fileList = ref([])
  const xmlContent = ref('')
  const xmlFilename = ref('')
  const fileCreatedAt = ref(null)

  /**
   * Before upload hook for XML file validation.
   * 
   * @param {File} file - File to validate
   * @returns {boolean} True if file is valid
   */
  const beforeUpload = (file) => {
    const isXml = file.name.toLowerCase().endsWith('.xml')
    const fileSizeMB = file.size / 1024 / 1024
    const isLt10M = fileSizeMB < 10

    if (!isXml) {
      ElMessage.error('Only XML files are supported!')
      return false
    }
    if (!isLt10M) {
      ElMessage.error({
        message: `File size is ${fileSizeMB.toFixed(2)}MB, which exceeds the 10MB limit. Please upload a smaller file.`,
        duration: 5000,
        showClose: true
      })
      return false
    }
    return true
  }

  /**
   * Handle file selection change.
   * 
   * @param {Object} file - File object from upload component
   */
  const handleFileChange = (file) => {
    uploadFile.value = file.raw
    fileList.value = [file]
  }

  /**
   * Handle file removal.
   */
  const handleRemove = () => {
    uploadFile.value = null
    fileList.value = []
    xmlContent.value = ''
    xmlFilename.value = ''
  }

  /**
   * Upload XML file to server.
   * 
   * @param {Function} [onSuccess] - Callback function called on success
   * @returns {Promise<boolean>} True if upload succeeded
   */
  const uploadXmlFile = async (onSuccess) => {
    if (!uploadFile.value) {
      ElMessage.warning('Please upload an XML file first!')
      return false
    }

    try {
      const formData = new FormData()
      formData.append('file', uploadFile.value)

      const response = await api.post('/upload-xml', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const data = response.data

      // Backend returns { message, data: { xml_content, filename, file_created_at } }
      if (data && data.data) {
        xmlContent.value = data.data.xml_content
        xmlFilename.value = data.data.filename
        fileCreatedAt.value = data.data.file_created_at
        
        ElMessage.success('XML file uploaded successfully!')
        
        if (onSuccess) {
          onSuccess(data.data.xml_content, data.data.filename, data.data.file_created_at)
        }
        return true
      } else {
        console.warn('Unexpected response format:', data)
        ElMessage.error('Unexpected response format from server')
        return false
      }
    } catch (error) {
      console.error('Upload Error:', error)
      ElMessage.error({
        message: `Failed to upload XML: ${error.response?.data?.message || error.message}`,
        duration: 5000,
        showClose: true
      })
      return false
    }
  }

  return {
    uploadFile,
    fileList,
    xmlContent,
    xmlFilename,
    fileCreatedAt,
    beforeUpload,
    handleFileChange,
    handleRemove,
    uploadXmlFile
  }
}

