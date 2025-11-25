<script setup>
/**
 * SessionWarning component for displaying session expiration warnings.
 * 
 * @component SessionWarning
 * @description Displays a warning when the uploaded file is approaching its expiration time.
 * Files expire after 30 minutes and a warning is shown when 5 minutes or less remain.
 * 
 * @props {number|null} fileCreatedAt - Timestamp when the file was created (in milliseconds)
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'

const showWarning = ref(false)
const remainingMinutes = ref(30)
const fileCreatedAt = ref(null)
let timer = null

const MAX_AGE_MINUTES = 30
const WARNING_THRESHOLD_MINUTES = 5

const updateTimer = () => {
  if (!fileCreatedAt.value) {
    return
  }

  const now = Date.now()
  const elapsedMinutes = (now - fileCreatedAt.value) / 1000 / 60
  const remaining = Math.max(0, MAX_AGE_MINUTES - Math.floor(elapsedMinutes))
  
  remainingMinutes.value = remaining
  
  // Show warning when 5 minutes or less remaining
  if (remaining <= WARNING_THRESHOLD_MINUTES) {
    showWarning.value = true
  } else {
    showWarning.value = false
  }
}

const setFileCreatedAt = (timestamp) => {
  // timestamp is server-returned second-level timestamp
  fileCreatedAt.value = timestamp * 1000 // Convert to milliseconds
  updateTimer()
}

const reset = () => {
  fileCreatedAt.value = null
  remainingMinutes.value = MAX_AGE_MINUTES
  showWarning.value = false
}

onMounted(() => {
  timer = setInterval(updateTimer, 30000) // Update every 30 seconds
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})

defineExpose({
  setFileCreatedAt,
  reset
})
</script>

<template>
  <div v-if="showWarning && remainingMinutes > 0" class="session-warning">
    <el-alert
      type="warning"
      :closable="false"
      show-icon
    >
      <template #title>
        <div class="warning-content">
          <el-icon><WarningFilled /></el-icon>
          <span>Files will be auto-deleted in {{ remainingMinutes }} minute(s). Please complete your work soon.</span>
        </div>
      </template>
    </el-alert>
  </div>
  <div v-else-if="showWarning && remainingMinutes === 0" class="session-warning">
    <el-alert
      type="error"
      :closable="false"
      show-icon
    >
      <template #title>
        <div class="warning-content">
          <el-icon><WarningFilled /></el-icon>
          <span>Session expired. Files have been deleted. Please re-upload to continue.</span>
        </div>
      </template>
    </el-alert>
  </div>
</template>

<style scoped>
.session-warning {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  max-width: 500px;
  animation: slideIn 0.3s ease;
  box-shadow: var(--shadow-md);
  transition: box-shadow 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.warning-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
