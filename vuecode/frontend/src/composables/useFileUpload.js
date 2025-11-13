import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useFileUpload() {
  const uploadFile = ref(null)
  const fileList = ref([])
  const ocrResult = ref(null)
  const ocrFilename = ref('')

  const beforeUpload = (file) => {
    // 检查文件扩展名
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png']
    const fileExtension = file.name.split('.').pop().toLowerCase()
    const isAllowedExtension = allowedExtensions.includes(fileExtension)
    
    // 检查MIME类型
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
    const isAllowedType = allowedTypes.includes(file.type)
    
    // 双重验证：扩展名和MIME类型都要检查
    if (!isAllowedExtension || !isAllowedType) {
      ElMessage.error({
        message: 'Only PDF, JPG, JPEG, and PNG files are supported!',
        duration: 5000,
        showClose: true
      })
      return false
    }
    
    // 检查文件大小
    const fileSizeMB = file.size / 1024 / 1024
    const isLt10M = fileSizeMB < 10
    
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

  const handleFileChange = (file) => {
    // 再次验证文件类型和大小（防止绕过beforeUpload）
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png']
    const fileExtension = file.name.split('.').pop().toLowerCase()
    const isAllowedExtension = allowedExtensions.includes(fileExtension)
    
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
    const isAllowedType = allowedTypes.includes(file.raw.type)
    
    const fileSizeMB = file.raw.size / 1024 / 1024
    const isLt10M = fileSizeMB < 10
    
    // 只有通过验证的文件才能被添加
    if (!isAllowedExtension || !isAllowedType) {
      ElMessage.error({
        message: 'Only PDF, JPG, JPEG, and PNG files are supported!',
        duration: 5000,
        showClose: true
      })
      return
    }
    
    if (!isLt10M) {
      ElMessage.error({
        message: `File size is ${fileSizeMB.toFixed(2)}MB, which exceeds the 10MB limit. Please upload a smaller file.`,
        duration: 5000,
        showClose: true
      })
      return
    }
    
    uploadFile.value = file.raw
    fileList.value = [file]
  }

  const handleRemove = () => {
    uploadFile.value = null
    fileList.value = []
  }

  const processOCR = async (onSuccess) => {
    if (!uploadFile.value) {
      ElMessage.warning('Please upload a file first!')
      return false
    }

    try {
      const formData = new FormData()
      formData.append('file', uploadFile.value)

      const response = await fetch('/api/ocr', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        const errorMsg = data.error || 'OCR processing failed'
        const details = data.message || (data.details ? data.details : '')
        const fullMessage = details ? `${details}` : errorMsg
        
        ElMessage.error({
          message: fullMessage,
          duration: 6000,
          showClose: true
        })
        return false
      }

      if (data.success && data.extracted) {
        ocrResult.value = data
        ocrFilename.value = data.json_filename || ''
        
        ElMessage.success('Document processed successfully!')
        
        if (onSuccess) {
          onSuccess(data.extracted, data.file_created_at)
        }
        return true
      } else {
        ElMessage.error('Unexpected response format')
        return false
      }
    } catch (error) {
      console.error('OCR Error:', error)
      ElMessage.error({
        message: `Failed to process document: ${error.message}`,
        duration: 5000,
        showClose: true
      })
      return false
    }
  }

  const downloadJSON = async () => {
    if (!ocrFilename.value) {
      ElMessage.warning('No JSON file available')
      return
    }
    
    try {
      const response = await fetch(`/api/download-json/${ocrFilename.value}`)
      
      if (!response.ok) {
        const data = await response.json()
        if (response.status === 404) {
          ElMessage.error({
            message: data.message || 'File has been deleted (auto-deleted after 30 minutes). Please re-upload and process the document.',
            duration: 6000,
            showClose: true
          })
        } else {
          ElMessage.error(data.error || 'Failed to download file')
        }
        return
      }
      
      const blob = await response.blob()
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
