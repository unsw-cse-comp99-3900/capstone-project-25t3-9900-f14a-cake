<script setup>
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
  color: #ffffff;
  margin-bottom: 0.5rem;
  text-align: center;
}

.section-subtitle {
  font-size: 0.95rem;
  color: #9ca3af;
  text-align: center;
  margin-bottom: 2.5rem;
}

.mode-selector {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 2rem;
  align-items: center;
  margin-bottom: 2.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.mode-option {
  text-align: center;
  padding: 1.5rem;
}

.mode-option h3 {
  font-size: 1.1rem;
  color: #10b981;
  margin-bottom: 0.5rem;
}

.mode-option p {
  font-size: 0.9rem;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.mode-divider {
  font-size: 1rem;
  font-weight: 600;
  color: #6b7280;
  padding: 0 1rem;
}

:deep(.uploader) { width: 100%; }

:deep(.el-upload-dragger) {
  background: rgba(16, 185, 129, 0.05);
  border: 2px dashed rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  padding: 3rem 2rem;
  width: 100%;
}

:deep(.el-upload-dragger:hover) {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}

/* 隐藏默认的文件列表 */
:deep(.el-upload-list) {
  display: none !important;
}

.upload-icon {
  font-size: 48px;
  color: #10b981;
  margin-bottom: 1rem;
}

.upload-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 0.5rem;
}

.upload-hint {
  font-size: 0.9rem;
  color: #6b7280;
}

.file-preview {
  margin-top: 1.5rem;
  padding: 1.25rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  transition: all 0.3s ease;
}

.file-preview:hover {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.3);
}

.file-icon { 
  font-size: 40px; 
  color: #10b981; 
  flex-shrink: 0;
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
  color: #ffffff; 
  margin-bottom: 0.35rem;
  font-weight: 500;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.file-size { 
  font-size: 0.9rem; 
  color: #9ca3af; 
}

.remove-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
  transition: all 0.3s ease;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: #ef4444;
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

