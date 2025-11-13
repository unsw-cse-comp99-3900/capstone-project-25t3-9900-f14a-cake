<script setup>
import { Upload, DocumentChecked } from '@element-plus/icons-vue'

defineProps({
  uploadFile: Object,
  fileList: Array
})

const emit = defineEmits(['before-upload', 'change', 'remove'])
</script>

<template>
  <div class="xml-upload-area">
    <h2 class="section-title">Upload XML Invoice</h2>
    <p class="section-subtitle">Upload an existing XML invoice file for validation</p>
    
    <el-upload
      class="uploader"
      drag
      :before-upload="(file) => emit('before-upload', file)"
      :on-change="(file) => emit('change', file)"
      :on-remove="() => emit('remove')"
      :file-list="fileList"
      :auto-upload="false"
      :limit="1"
      accept=".xml"
    >
      <el-icon class="upload-icon"><Upload /></el-icon>
      <div class="upload-text">
        <div class="upload-title">Drop XML file here or click to upload</div>
        <div class="upload-hint">Only .xml files are supported (Max: 10MB)</div>
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
.xml-upload-area {
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
  font-size: 1.05rem;
  color: #d1d5db;
  text-align: center;
  margin-bottom: 2.5rem;
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
  font-size: 1rem;
  color: #cbd5e1;
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
  font-size: 1rem; 
  color: #d1d5db; 
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
</style>

