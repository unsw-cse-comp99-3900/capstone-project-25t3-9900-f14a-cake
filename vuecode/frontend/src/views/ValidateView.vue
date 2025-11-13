<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useXmlUpload } from '@/composables/useXmlUpload'
import XmlUploader from '@/components/XmlUploader.vue'
import EmailSender from '@/components/EmailSender.vue'
import SessionWarning from '@/components/SessionWarning.vue'

const router = useRouter()
const currentStep = ref(0)
const isProcessing = ref(false)
const emailSent = ref(false)
const sessionWarningRef = ref(null)

const {
  uploadFile,
  fileList,
  xmlContent,
  xmlFilename,
  beforeUpload,
  handleFileChange,
  handleRemove,
  uploadXmlFile
} = useXmlUpload()

const validationResult = ref(null)
const isValidating = ref(false)

const steps = [
  { title: 'Upload', description: 'Upload XML file' },
  { title: 'Validate', description: 'Validate XML' },
  { title: 'Send', description: 'Send via email' },
]

const goBack = () => {
  router.push('/')
}

const handleUploadSuccess = (content, filename, createdAt) => {
  if (sessionWarningRef.value && createdAt) {
    sessionWarningRef.value.setFileCreatedAt(createdAt)
  }
  
  currentStep.value = 1
  
  setTimeout(() => {
    handleValidate()
  }, 500)
}

const handleUpload = async () => {
  isProcessing.value = true
  await uploadXmlFile(handleUploadSuccess)
  isProcessing.value = false
}

const handleValidate = async () => {
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
    
    if (data.results && data.results.token_refreshed) {
      ElMessage.info({
        message: 'Authentication token was refreshed automatically.',
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

const getAssertionErrors = (result) => {
  if (!result.response_body) return []
  
  const reports = result.response_body.report?.reports
  if (!reports) return []
  
  for (const ruleName in reports) {
    const ruleReport = reports[ruleName]
    if (ruleReport.firedAssertionErrors && Array.isArray(ruleReport.firedAssertionErrors)) {
      return ruleReport.firedAssertionErrors
    }
  }
  
  return []
}

const getReportSummary = (result) => {
  if (!result.response_body) return result.message
  
  const summary = result.response_body.report?.summary
  return summary || result.message
}

const downloadResponseBody = (ruleName, responseBody) => {
  try {
    const content = JSON.stringify(responseBody, null, 2)
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ruleName}_validation_response.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('Response downloaded!')
  } catch (error) {
    console.error('Download error:', error)
    ElMessage.error('Failed to download response')
  }
}

const sendEmail = async (email) => {
  if (!email) {
    ElMessage.warning('Please enter an email address')
    return
  }
  
  if (!xmlFilename.value) {
    ElMessage.warning('Please upload XML first')
    return
  }
  
  isProcessing.value = true
  
  try {
    const response = await fetch('/api/send-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        xml_filename: xmlFilename.value
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      if (response.status === 404) {
        ElMessage.error({
          message: data.message || 'XML file has been deleted.',
          duration: 6000,
          showClose: true
        })
      } else if (data.error_info) {
        ElMessageBox.alert(
          `<div style="line-height: 1.6;">
            <p><strong>${data.error_info.title}</strong></p>
            <p style="margin: 1rem 0;">${data.error_info.message}</p>
            <p style="color: #9ca3af; font-size: 0.9em;">${data.error_info.details}</p>
          </div>`,
          'Email Sending Failed',
          {
            dangerouslyUseHTMLString: true,
            confirmButtonText: 'OK',
            type: 'error'
          }
        )
      } else {
        ElMessage.error(data.error || 'Failed to send email')
      }
      return
    }

    if (data.success) {
      emailSent.value = true
      currentStep.value = 3
      ElMessage.success({
        message: data.message,
        duration: 5000,
        showClose: true
      })
    }
  } catch (error) {
    console.error('Email Error:', error)
    ElMessage.error(`Failed to send email: ${error.message}`)
  } finally {
    isProcessing.value = false
  }
}

const startOver = () => {
  currentStep.value = 0
  uploadFile.value = null
  fileList.value = []
  xmlContent.value = ''
  xmlFilename.value = ''
  validationResult.value = null
  emailSent.value = false
  
  if (sessionWarningRef.value) {
    sessionWarningRef.value.reset()
  }
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    await handleUpload()
  } else if (currentStep.value === 1) {
    if (!validationResult.value || !validationResult.value.success) {
      ElMessage.error('XML validation failed. Please fix the errors before proceeding.')
      return
    }
    currentStep.value = 2
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    
    if (currentStep.value === 0) {
      validationResult.value = null
    }
  }
}
</script>

<template>
  <div class="validate-page">
    <SessionWarning ref="sessionWarningRef" />

    <header class="header">
      <div class="header-content">
        <h1 class="page-title">XML Invoice Validation</h1>
        <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack">
          Back to Home
        </el-button>
      </div>
    </header>

    <main class="main-content">
      <div class="steps">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{ active: index === currentStep, completed: index < currentStep }"
        >
          <div class="step-indicator">
            <span v-if="index < currentStep">✓</span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="step-info">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-desc">{{ step.description }}</div>
          </div>
        </div>
      </div>

      <div class="content-card">
        <!-- Step 0: Upload XML -->
        <div v-show="currentStep === 0" class="step-content">
          <XmlUploader
            :upload-file="uploadFile"
            :file-list="fileList"
            @before-upload="beforeUpload"
            @change="handleFileChange"
            @remove="handleRemove"
          />
        </div>

        <!-- Step 1: Validate XML -->
        <div v-show="currentStep === 1" class="step-content">
          <h2 class="section-title">XML Validation Results</h2>
          <p class="section-subtitle">Validating against AUNZ_UBL and AUNZ_PEPPOL standards</p>
          
          <div v-if="isValidating" class="validating">
            <el-icon class="rotating" :size="40">
              <Loading />
            </el-icon>
            <span>Validating XML...</span>
          </div>
          
          <div v-else-if="validationResult" class="validation-results">
            <el-alert 
              :type="validationResult.success ? 'success' : 'error'"
              :title="validationResult.success ? 'Validation Passed' : 'Validation Failed'"
              :closable="false"
              show-icon
              class="main-status"
            >
              {{ validationResult.success ? 'All validation rules passed successfully!' : 'Some validation rules failed. Please check the details below.' }}
            </el-alert>

            <div class="rules-details">
              <div 
                v-for="(result, rule) in validationResult.results" 
                :key="rule"
                class="rule-card"
                :class="{ success: result.successful, error: !result.successful }"
              >
                <div class="rule-header">
                  <span class="rule-name">{{ rule }}</span>
                  <el-tag :type="result.successful ? 'success' : 'danger'" size="small">
                    {{ result.successful ? 'PASSED' : 'FAILED' }}
                  </el-tag>
                </div>
                <div class="rule-body">
                  <div v-if="result.successful" class="success-info">
                    <p class="success-text">✓ Validation successful</p>
                  </div>
                  
                  <div v-else class="error-info">
                    <div 
                      v-if="getAssertionErrors(result).length > 0" 
                      class="assertion-errors"
                    >
                      <div class="error-header">
                        <strong>Validation Errors ({{ getAssertionErrors(result).length }}):</strong>
                      </div>
                      <div 
                        v-for="(error, index) in getAssertionErrors(result)" 
                        :key="index"
                        class="error-item"
                      >
                        <div class="error-id">{{ error.id }}</div>
                        <div class="error-text">{{ error.text }}</div>
                      </div>
                    </div>
                    
                    <div v-else class="general-error">
                      <p>{{ result.message }}</p>
                      <p v-if="result.error" class="error-details">{{ result.error }}</p>
                    </div>
                  </div>
                  
                  <div v-if="result.response_body" class="response-actions">
                    <el-button 
                      size="small" 
                      type="info"
                      plain
                      @click="downloadResponseBody(rule, result.response_body)"
                    >
                      Download Full Response (JSON)
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2 & 3: Send Email -->
        <div v-show="currentStep === 2 || currentStep === 3" class="step-content">
          <EmailSender
            :xml-filename="xmlFilename"
            :email-sent="emailSent"
            :is-loading="isProcessing"
            @download="downloadXML"
            @send="sendEmail"
            @start-over="startOver"
          />
        </div>
      </div>

      <!-- Actions -->
      <div v-if="!emailSent" class="actions">
        <el-button 
          v-if="currentStep > 0 && currentStep < 2"
          size="large" 
          @click="prevStep"
        >
          Previous
        </el-button>
        <el-button 
          v-if="currentStep < 2"
          type="primary" 
          size="large" 
          :loading="isProcessing"
          :disabled="(!uploadFile && currentStep === 0) || (currentStep === 1 && (!validationResult || !validationResult.success))"
          @click="nextStep"
        >
          {{ currentStep === 0 ? 'Upload & Validate' : 'Proceed to Send' }}
        </el-button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.validate-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
  padding-top: 0;
}

.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(15, 20, 25, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1.25rem 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #10b981;
  margin: 0;
}

.back-btn {
  color: #10b981 !important;
  background-color: rgba(16, 185, 129, 0.08) !important;
  border-color: rgba(16, 185, 129, 0.25) !important;
  border-width: 1px;
  border-style: solid;
  border-radius: 8px;
  padding: 0.4rem 0.6rem;
  transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.back-btn:hover {
  background-color: rgba(16, 185, 129, 0.18) !important;
  border-color: #10b981 !important;
}

.back-btn:focus-visible {
  outline: 2px solid rgba(16, 185, 129, 0.5);
  outline-offset: 2px;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2.5rem 2rem;
}

.steps {
  display: flex;
  justify-content: center;
  margin-bottom: 2.5rem;
  gap: 2rem;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

.step {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  opacity: 0.5;
  transition: opacity 0.3s ease;
  min-width: 200px;
}

.step.active,
.step.completed {
  opacity: 1;
}

.step-indicator {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #6b7280;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.step.active .step-indicator {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10b981;
  color: #10b981;
}

.step.completed .step-indicator {
  background: #10b981;
  border-color: #10b981;
  color: #ffffff;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 0.25rem;
}

.step-desc {
  font-size: 0.8rem;
  color: #6b7280;
}

.content-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 2.5rem;
  min-height: 400px;
}

.step-content {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 0.5rem;
  text-align: center;
}

.section-subtitle {
  font-size: 0.95rem;
  color: #9ca3af;
  text-align: center;
  margin-bottom: 2rem;
}

.validating {
  text-align: center;
  padding: 3rem;
  color: #10b981;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.validation-results {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.main-status {
  font-size: 1rem;
}

.rules-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.rule-card {
  padding: 1.25rem;
  border-radius: 12px;
  border: 1px solid;
}

.rule-card.success {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.rule-card.error {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.rule-name {
  font-weight: 600;
  color: #ffffff;
  font-size: 0.95rem;
}

.rule-body {
  font-size: 1rem;
}

.success-info {
  padding: 1rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  border-left: 3px solid #10b981;
}

.success-text {
  color: #10b981;
  font-weight: 600;
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
}

.error-info {
  margin-top: 0.5rem;
}

.assertion-errors {
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  padding: 1rem;
  border-left: 3px solid #ef4444;
}

.error-header {
  color: #ef4444;
  margin-bottom: 1rem;
  font-size: 0.95rem;
}

.error-item {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
}

.error-item:last-child {
  margin-bottom: 0;
}

.error-id {
  color: #f59e0b;
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.error-text {
  color: #ffffff;
  line-height: 1.6;
  font-size: 1rem;
}

.general-error {
  padding: 1rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  border-left: 3px solid #ef4444;
}

.general-error p {
  color: #ef4444;
  margin: 0;
  line-height: 1.5;
}

.error-details {
  margin-top: 0.5rem;
  color: #d1d5db !important;
  font-size: 1rem;
}

.response-actions {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 0.75rem;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .steps {
    flex-direction: column;
  }

  .content-card {
    padding: 1.5rem;
  }

  .rules-details {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column;
  }

  .actions .el-button {
    width: 100%;
  }
}
</style>
