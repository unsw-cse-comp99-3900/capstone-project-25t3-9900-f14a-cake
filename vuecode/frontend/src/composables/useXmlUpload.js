import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useXmlUpload() {
  const uploadFile = ref(null)
  const fileList = ref([])
  const xmlContent = ref('')
  const xmlFilename = ref('')
  const fileCreatedAt = ref(null)

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

  const handleFileChange = (file) => {
    uploadFile.value = file.raw
    fileList.value = [file]
  }

  const handleRemove = () => {
    uploadFile.value = null
    fileList.value = []
    xmlContent.value = ''
    xmlFilename.value = ''
  }

  const uploadXmlFile = async (onSuccess) => {
    if (!uploadFile.value) {
      ElMessage.warning('Please upload an XML file first!')
      return false
    }

    try {
      const formData = new FormData()
      formData.append('file', uploadFile.value)

      const response = await fetch('/api/upload-xml', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        if (response.status === 413) {
          ElMessage.error({
            message: 'File size exceeds the 10MB limit. Please upload a smaller file.',
            duration: 6000,
            showClose: true
          })
          return false
        }
        
        const errorMsg = data.error || 'Failed to upload XML'
        const details = data.message ? `\n${data.message}` : ''
        ElMessage.error({
          message: errorMsg + details,
          duration: 5000,
          showClose: true
        })
        return false
      }

      if (data.success) {
        xmlContent.value = data.xml_content
        xmlFilename.value = data.filename
        fileCreatedAt.value = data.file_created_at
        
        ElMessage.success('XML file uploaded successfully!')
        
        if (onSuccess) {
          onSuccess(data.xml_content, data.filename, data.file_created_at)
        }
        return true
      } else {
        ElMessage.error('Unexpected response format')
        return false
      }
    } catch (error) {
      console.error('Upload Error:', error)
      ElMessage.error({
        message: `Failed to upload XML: ${error.message}`,
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

