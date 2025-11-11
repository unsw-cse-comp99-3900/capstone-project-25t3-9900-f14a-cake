import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useFileUpload() {
  const uploadFile = ref(null)
  const fileList = ref([])
  const ocrResult = ref(null)
  const ocrFilename = ref('')

  const beforeUpload = (file) => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg']
    const isAllowedType = allowedTypes.includes(file.type)
    const isLt10M = file.size / 1024 / 1024 < 10

    if (!isAllowedType) {
      ElMessage.error('Only PDF, JPG, and JPEG files are supported!')
      return false
    }
    if (!isLt10M) {
      ElMessage.error('File size cannot exceed 10MB!')
      return false
    }
    return true
  }

  const handleFileChange = (file) => {
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
        const details = data.details ? `\n${data.details}` : ''
        ElMessage.error({
          message: errorMsg + details,
          duration: 5000,
          showClose: true
        })
        return false
      }

      if (data.success && data.extracted) {
        ocrResult.value = data
        ocrFilename.value = data.json_filename || ''
        
        ElMessage.success('Document processed successfully!')
        
        if (onSuccess) {
          onSuccess(data.extracted)
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

  const downloadJSON = () => {
    if (!ocrFilename.value) {
      ElMessage.warning('No JSON file available')
      return
    }
    
    const url = `/api/download-json/${ocrFilename.value}`
    const a = document.createElement('a')
    a.href = url
    a.download = ocrFilename.value
    a.click()
    ElMessage.success('Downloading JSON file...')
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

