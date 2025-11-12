<script setup>
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
  // 从响应体中提取 firedAssertionErrors
  if (!result.response_body) return []
  
  const reports = result.response_body.report?.reports
  if (!reports) return []
  
  // 查找对应规则的报告
  for (const ruleName in reports) {
    const ruleReport = reports[ruleName]
    if (ruleReport.firedAssertionErrors && Array.isArray(ruleReport.firedAssertionErrors)) {
      return ruleReport.firedAssertionErrors
    }
  }
  
  return []
}

const getReportSummary = (result) => {
  // 从响应体中提取 report.summary
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
    
    <!-- 生成按钮 -->
    <div v-if="!xmlContent" class="preview-action">
      <el-button 
        type="primary" 
        size="large"
        @click="emit('generate')"
      >
        Generate XML
      </el-button>
    </div>

    <!-- XML预览和验证结果 -->
    <div v-else class="validation-area">
      <!-- XML内容 -->
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

      <!-- 验证状态 -->
      <div class="validation-status">
        <div v-if="isValidating" class="validating">
          <el-icon class="rotating"><Loading /></el-icon>
          <span>Validating XML...</span>
        </div>
        
        <div v-else-if="validationResult" class="validation-results">
          <!-- 整体状态 -->
          <el-alert 
            :type="validationResult.success ? 'success' : 'error'"
            :title="validationResult.success ? 'Validation Passed' : 'Validation Failed'"
            :closable="false"
            show-icon
            class="main-status"
          >
            {{ validationResult.success ? 'All validation rules passed successfully!' : 'Some validation rules failed. Please check the details below.' }}
          </el-alert>

          <!-- 各规则详情 -->
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
                    <!-- 成功状态 -->
                    <div v-if="result.successful" class="success-info">
                      <p class="success-text">✓ Validation successful</p>
                    </div>
                
                <!-- 失败状态 -->
                <div v-else class="error-info">
                  <!-- 提取并显示assertion errors -->
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
                  
                  <!-- 如果没有assertion errors，显示一般错误信息 -->
                  <div v-else class="general-error">
                    <p>{{ result.message }}</p>
                    <p v-if="result.error" class="error-details">{{ result.error }}</p>
                  </div>
                </div>
                
                <!-- 下载完整响应体 -->
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

<style scoped>
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
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  overflow: hidden;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(16, 185, 129, 0.1);
}

.viewer-title {
  font-weight: 600;
  color: #10b981;
}

.viewer-content {
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  max-height: 500px;
  overflow-y: auto;
}

.viewer-content pre {
  color: #9ca3af;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
}

.validation-status {
  margin-top: 1rem;
}

.validating {
  text-align: center;
  padding: 2rem;
  color: #10b981;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
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
  font-size: 0.9rem;
}

.rule-message {
  color: #9ca3af;
  margin: 0;
  line-height: 1.5;
}

.rule-error {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  color: #ef4444;
  font-size: 0.85rem;
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
  font-size: 0.9rem;
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
  color: #9ca3af !important;
  font-size: 0.9rem;
}

.response-actions {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.no-validation {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
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

