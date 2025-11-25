<script setup>
/**
 * FileUploader component for uploading invoice documents.
 * 
 * @component FileUploader
 * @description Provides file upload interface for invoice documents (PDF, JPG, JPEG, PNG).
 * Supports both auto-extract mode (OCR) and manual entry mode.
 * Validates file type and size before upload.
 * 
 * @props {Object} uploadFile - Currently uploaded file object
 * @props {Array} fileList - List of uploaded files
 * 
 * @emits {File} before-upload - Emitted before file upload with file object
 * @emits {Object} change - Emitted when file selection changes
 * @emits {void} remove - Emitted when file is removed
 * @emits {void} skip-to-manual - Emitted when user chooses manual entry mode
 */
import { Upload, DocumentChecked, Edit } from '@element-plus/icons-vue'

defineProps({
  uploadFile: Object,
  fileList: Array
})

const emit = defineEmits(['before-upload', 'change', 'remove', 'skip-to-manual'])
</script>

<template>
  <div class="upload-area">
    <h2 class="section-title">Upload Invoice Document</h2>
    <p class="section-subtitle">Upload a file to auto-extract information, or enter data manually (Supported: PDF, JPG, JPEG, PNG)</p>
    
    <div class="mode-selector">
      <div class="mode-option">
        <h3>Option 1: Auto Extract</h3>
        <p>Upload PDF or image to automatically extract invoice data</p>
      </div>
      <div class="mode-divider">OR</div>
      <div class="mode-option">
        <h3>Option 2: Manual Entry</h3>
        <el-button 
          type="primary" 
          plain
          :icon="Edit"
          size="large"
          @click="emit('skip-to-manual')"
        >
          Enter Data Manually
        </el-button>
      </div>
    </div>
    
    <el-upload
      class="uploader"
      drag
      :before-upload="(file) => emit('before-upload', file)"
      :on-change="(file) => emit('change', file)"
      :on-remove="() => emit('remove')"
      :file-list="fileList"
      :auto-upload="false"
      :limit="1"
    >
      <el-icon class="upload-icon"><Upload /></el-icon>
              <div class="upload-text">
                <div class="upload-title">Drop file here or click to upload</div>
                <div class="upload-hint">PDF, JPG, JPEG, PNG up to 10MB</div>
              </div>
    </el-upload>

    <div v-if="uploadFile" class="file-preview">
      <el-icon class="file-icon"><DocumentChecked /></el-icon>
      <div class="file-details">
        <div class="file-info">
          <div class="file-name">{{ uploadFile.name }}</div>
          <div class="file-size">{{ (uploadFile.size / 1024).toFixed(2) }} KB</div>
        </div>
        <el-button 
          type="danger" 
          circle
          size="large"
          class="remove-btn"
          @click="emit('remove')"
        >
          <el-icon :size="18">✕</el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-area {
  max-width: 700px;
  margin: 0 auto;
}

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
  margin-bottom: 2.5rem;
  transition: color 0.3s ease;
}

.mode-selector {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 2rem;
  align-items: center;
  margin-bottom: 2.5rem;
  padding: 1rem;
  background: var(--bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--border-primary);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.mode-option {
  text-align: center;
  padding: 1.5rem;
}

.mode-option h3 {
  font-size: 1.1rem;
  color: var(--accent-primary);
  margin-bottom: 0.5rem;
  transition: color 0.3s ease;
}

.mode-option p {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
  transition: color 0.3s ease;
}

.mode-divider {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-tertiary);
  padding: 0 1rem;
  transition: color 0.3s ease;
}

:deep(.uploader) { width: 100%; }

:deep(.el-upload-dragger) {
  background: var(--bg-hover);
  border: 2px dashed var(--border-accent);
  border-radius: 12px;
  padding: 3rem 2rem;
  width: 100%;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--accent-primary);
  background: var(--bg-active);
}

/* Hide default file list */
:deep(.el-upload-list) {
  display: none !important;
}

.upload-icon {
  font-size: 48px;
  color: var(--accent-primary);
  margin-bottom: 1rem;
  transition: color 0.3s ease;
}

.upload-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  transition: color 0.3s ease;
}

.upload-hint {
  font-size: 0.9rem;
  color: var(--text-tertiary);
  transition: color 0.3s ease;
}

.file-preview {
  margin-top: 1.5rem;
  padding: 1.25rem;
  background: var(--bg-hover);
  border: 1px solid var(--border-accent);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  transition: all 0.3s ease;
}

.file-preview:hover {
  background: var(--bg-active);
  border-color: var(--border-accent);
}

.file-icon { 
  font-size: 40px; 
  color: var(--accent-primary); 
  flex-shrink: 0;
  transition: color 0.3s ease;
}

.file-details { 
  flex: 1; 
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name { 
  font-size: 1rem; 
  color: var(--text-primary); 
  margin-bottom: 0.35rem;
  font-weight: 500;
  word-wrap: break-word;
  overflow-wrap: break-word;
  transition: color 0.3s ease;
}

.file-size { 
  font-size: 0.9rem; 
  color: var(--text-secondary); 
  transition: color 0.3s ease;
}

.remove-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--accent-danger);
  transition: all 0.3s ease;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: var(--accent-danger);
  transform: scale(1.1);
}

@media (max-width: 768px) {
  .mode-selector {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .mode-divider {
    padding: 0.5rem 0;
  }

  .mode-option {
    padding: 1rem;
  }
}
</style>

