<script setup>
/**
 * XmlValidator component for displaying XML validation results.
 * 
 * @component XmlValidator
 * @description Displays XML validation results from ESS Validator API.
 * Shows validation status, errors, warnings, and allows downloading XML.
 * Supports both success and failure validation states.
 * 
 * @props {string} xmlContent - XML content to validate
 * @props {string} xmlFilename - XML filename
 * @props {Object} validationResult - Validation result object from API
 * @props {boolean} isValidating - Whether validation is in progress
 * 
 * @emits {void} download - Emitted when download XML button is clicked
 * @emits {void} generate - Emitted when generate XML button is clicked
 */
import { Download, Loading } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'

defineProps({
  xmlContent: String,
  xmlFilename: String,
  validationResult: Object,
  isValidating: Boolean
})

const emit = defineEmits(['download', 'generate'])

const getAssertionErrors = (result) => {
  // Extract firedAssertionErrors from response body
  if (!result.response_body) return []
  
  const reports = result.response_body.report?.reports
  if (!reports) return []
  
  // Find corresponding rule report
  for (const ruleName in reports) {
    const ruleReport = reports[ruleName]
    if (ruleReport.firedAssertionErrors && Array.isArray(ruleReport.firedAssertionErrors)) {
      return ruleReport.firedAssertionErrors
    }
  }
  
  return []
}

const getReportSummary = (result) => {
  // Extract report.summary from response body
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
</script>

<template>
  <div>
    <h2 class="section-title">Generate & Validate XML</h2>
    <p class="section-subtitle">Generate UBL-compliant XML and validate against AUNZ rules</p>
    
    <!-- Generate button -->
    <div v-if="!xmlContent" class="preview-action">
      <el-button 
        type="primary" 
        size="large"
        @click="emit('generate')"
      >
        Generate XML
      </el-button>
    </div>

    <!-- XML preview and validation results -->
    <div v-else class="validation-area">
      <!-- XML content -->
      <div class="xml-viewer">
        <div class="viewer-header">
          <span class="viewer-title">Generated XML Content</span>
          <el-button :icon="Download" size="small" @click="emit('download')">
            Download
          </el-button>
        </div>
        <div class="viewer-content">
          <pre>{{ xmlContent }}</pre>
        </div>
      </div>

      <!-- Validation status -->
      <div class="validation-status">
        <div v-if="isValidating" class="validating">
          <el-icon class="rotating"><Loading /></el-icon>
          <span>Validating XML...</span>
        </div>
        
        <div v-else-if="validationResult" class="validation-results">
          <!-- Overall status -->
          <el-alert 
            :type="validationResult.success ? 'success' : 'error'"
            :title="validationResult.success ? 'Validation Passed' : 'Validation Failed'"
            :closable="false"
            show-icon
            class="main-status"
          >
            {{ validationResult.success ? 'All validation rules passed successfully!' : 'Some validation rules failed. Please check the details below.' }}
          </el-alert>

          <!-- Rule details -->
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
                    <!-- Success state -->
                    <div v-if="result.successful" class="success-info">
                      <p class="success-text">✓ Validation successful</p>
                    </div>
                
                <!-- Failure state -->
                <div v-else class="error-info">
                  <!-- Extract and display assertion errors -->
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
                  
                  <!-- If no assertion errors, display general error message -->
                  <div v-else class="general-error">
                    <p>{{ result.message }}</p>
                    <p v-if="result.error" class="error-details">{{ result.error }}</p>
                  </div>
                </div>
                
                <!-- Download complete response body -->
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

        <div v-else class="no-validation">
          <p>Generating XML and starting validation...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Global styles for validation success alerts and tags - theme-aware */
:root[data-theme="light"] .main-status.el-alert--success.is-light {
  background-color: rgba(16, 185, 129, 0.15) !important;
  border-color: rgba(5, 150, 105, 0.4) !important;
}

:root[data-theme="light"] .main-status.el-alert--success.is-light .el-alert__title {
  color: #059669 !important; /* Darker green for better contrast */
  font-weight: 600;
}

:root[data-theme="light"] .main-status.el-alert--success.is-light .el-alert__description {
  color: #047857 !important; /* Even darker green for description */
}

:root[data-theme="light"] .main-status.el-alert--success.is-light .el-alert__icon {
  color: #059669 !important; /* Darker green for icon */
}

:root[data-theme="dark"] .main-status.el-alert--success.is-light {
  background-color: rgba(16, 185, 129, 0.1) !important;
  border-color: rgba(16, 185, 129, 0.2) !important;
}

:root[data-theme="dark"] .main-status.el-alert--success.is-light .el-alert__title {
  color: #10b981 !important; /* Light green for dark mode */
  font-weight: 600;
}

:root[data-theme="dark"] .main-status.el-alert--success.is-light .el-alert__description {
  color: #34d399 !important; /* Lighter green for description in dark mode */
}

:root[data-theme="dark"] .main-status.el-alert--success.is-light .el-alert__icon {
  color: #10b981 !important; /* Light green for icon in dark mode */
}

:root[data-theme="light"] .validation-results .el-tag.el-tag--success {
  background-color: rgba(5, 150, 105, 0.2) !important;
  border-color: rgba(5, 150, 105, 0.5) !important;
  color: #047857 !important; /* Dark green text */
  font-weight: 600;
}

:root[data-theme="dark"] .validation-results .el-tag.el-tag--success {
  background-color: rgba(16, 185, 129, 0.15) !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
  color: #10b981 !important; /* Light green text for dark mode */
  font-weight: 500;
}
</style>

<style scoped>
.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  text-align: center;
  transition: color 0.3s ease;
}

.section-subtitle {
  font-size: 0.95rem;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 2rem;
  transition: color 0.3s ease;
}

.preview-action {
  display: flex;
  justify-content: center;
  margin-top: 3rem;
}

.validation-area {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.xml-viewer {
  border: 1px solid var(--border-accent);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-hover);
  transition: background-color 0.3s ease;
}

.viewer-title {
  font-weight: 600;
  color: var(--accent-primary);
  transition: color 0.3s ease;
}

.viewer-content {
  padding: 1.5rem;
  background: var(--bg-section);
  max-height: 500px;
  overflow-y: auto;
  transition: background-color 0.3s ease;
}

.viewer-content pre {
  color: var(--text-muted);
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
  transition: color 0.3s ease;
}

.validation-status {
  margin-top: 1rem;
}

.validating {
  text-align: center;
  padding: 2rem;
  color: var(--accent-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  transition: color 0.3s ease;
}

.rotating {
  font-size: 32px;
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
  background: var(--bg-hover);
  border-color: var(--border-accent);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.rule-card.error {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.rule-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.95rem;
  transition: color 0.3s ease;
}

.rule-body {
  font-size: 0.9rem;
}

.rule-message {
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
  transition: color 0.3s ease;
}

.rule-error {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: var(--bg-section);
  border-radius: 6px;
  color: var(--accent-danger);
  font-size: 0.85rem;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.success-info {
  padding: 1rem;
  background: var(--bg-hover);
  border-radius: 8px;
  border-left: 3px solid var(--accent-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.success-text {
  color: var(--accent-primary);
  font-weight: 600;
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
  transition: color 0.3s ease;
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
  color: var(--accent-danger);
  margin-bottom: 1rem;
  font-size: 0.95rem;
  transition: color 0.3s ease;
}

.error-item {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--bg-section);
  border-radius: 6px;
  transition: background-color 0.3s ease;
}

.error-item:last-child {
  margin-bottom: 0;
}

.error-id {
  color: var(--accent-warning);
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: anywhere;
  transition: color 0.3s ease;
}

.error-text {
  color: var(--text-primary);
  line-height: 1.6;
  font-size: 0.9rem;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  transition: color 0.3s ease;
}

.general-error {
  padding: 1rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  border-left: 3px solid var(--accent-danger);
  transition: border-color 0.3s ease;
}

.general-error p {
  color: var(--accent-danger);
  margin: 0;
  line-height: 1.5;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  transition: color 0.3s ease;
}

.error-details {
  margin-top: 0.5rem;
  color: var(--text-secondary) !important;
  font-size: 0.9rem;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  transition: color 0.3s ease;
}

.response-actions {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-primary);
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  transition: border-color 0.3s ease;
}

.no-validation {
  text-align: center;
  padding: 2rem;
  color: var(--text-tertiary);
  transition: color 0.3s ease;
}

:deep(.response-dialog) {
  max-width: 800px;
  width: 90%;
}

:deep(.response-dialog .el-message-box__message) {
  max-height: 500px;
  overflow-y: auto;
}
</style>

