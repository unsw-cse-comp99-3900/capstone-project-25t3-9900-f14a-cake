<script setup>
import { Download, Loading } from '@element-plus/icons-vue'

defineProps({
  xmlContent: String,
  xmlFilename: String,
  validationResult: Object,
  isValidating: Boolean
})

const emit = defineEmits(['download', 'generate'])
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
                <p class="rule-message">{{ result.message }}</p>
                <div v-if="!result.successful && result.error" class="rule-error">
                  <strong>Error:</strong> {{ result.error }}
                </div>
                <div v-if="result.assertion_errors_count > 0" class="rule-stats">
                  <span>Assertion Errors: {{ result.assertion_errors_count }}</span>
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

.rule-stats {
  margin-top: 0.5rem;
  color: #f59e0b;
  font-size: 0.85rem;
}

.no-validation {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}
</style>

