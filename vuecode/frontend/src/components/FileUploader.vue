<script setup>
import { Upload, DocumentChecked } from '@element-plus/icons-vue'

defineProps({
  uploadFile: Object,
  fileList: Array
})

const emit = defineEmits(['before-upload', 'change', 'remove'])
</script>

<template>
  <div class="upload-area">
    <h2 class="section-title">Upload Invoice Document</h2>
    <p class="section-subtitle">Supported formats: PDF, JPG, JPEG (Max: 10MB)</p>
    
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
        <div class="upload-hint">PDF, JPG, JPEG up to 10MB</div>
      </div>
    </el-upload>

    <div v-if="uploadFile" class="file-preview">
      <el-icon class="file-icon"><DocumentChecked /></el-icon>
      <div class="file-details">
        <div class="file-name">{{ uploadFile.name }}</div>
        <div class="file-size">{{ (uploadFile.size / 1024).toFixed(2) }} KB</div>
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
  margin-bottom: 2rem;
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
  padding: 1rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon { font-size: 32px; color: #10b981; }
.file-details { flex: 1; }
.file-name { font-size: 0.95rem; color: #ffffff; margin-bottom: 0.25rem; }
.file-size { font-size: 0.85rem; color: #6b7280; }
</style>

