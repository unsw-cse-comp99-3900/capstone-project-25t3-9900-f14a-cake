import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useXmlOperations() {
  const xmlContent = ref('')
  const xmlFilename = ref('')
  const validationResult = ref(null)
  const isValidating = ref(false)

  const generateXML = async (invoiceData, onSuccess) => {
    try {
      const response = await fetch('/api/generate-xml', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(invoiceData),
      })

      const data = await response.json()

      if (!response.ok) {
        ElMessage.error(data.error || 'Failed to generate XML')
        return false
      }

      if (data.success) {
        xmlContent.value = data.xml_content
        xmlFilename.value = data.filename
        ElMessage.success('XML generated successfully!')
        
        // 自动验证
        await validateXML()
        
        if (onSuccess) {
          onSuccess()
        }
        return true
      }
      return false
    } catch (error) {
      console.error('XML Generation Error:', error)
      ElMessage.error(`Failed to generate XML: ${error.message}`)
      return false
    }
  }

  const validateXML = async () => {
    if (!xmlContent.value) {
      ElMessage.warning('No XML content to validate')
      return false
    }

    isValidating.value = true
    
    try {
      const response = await fetch('/api/validate-xml', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          xml_content: xmlContent.value
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        ElMessage.error(data.error || 'Failed to validate XML')
        validationResult.value = { success: false, error: data.error }
        return false
      }

      validationResult.value = data
      
      if (data.success) {
        ElMessage.success('XML validation passed!')
        return true
      } else {
        ElMessage.warning('XML validation failed. Please check the errors.')
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

  const downloadXML = () => {
    if (!xmlContent.value) {
      ElMessage.warning('No XML content available')
      return
    }
    
    const blob = new Blob([xmlContent.value], { type: 'application/xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = xmlFilename.value || 'invoice.xml'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('XML downloaded!')
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

