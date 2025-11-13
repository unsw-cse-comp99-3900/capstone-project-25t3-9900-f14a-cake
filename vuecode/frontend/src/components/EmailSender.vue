<script setup>
import { ref } from 'vue'
import { Download, Check, Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  xmlFilename: {
    type: String,
    required: true
  },
  emailSent: {
    type: Boolean,
    default: false
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['download', 'send', 'startOver'])

const recipientEmail = ref('')
const isValidEmail = ref(false)

const validateEmail = () => {
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  isValidEmail.value = emailPattern.test(recipientEmail.value)
  return isValidEmail.value
}

const handleSend = () => {
  if (validateEmail()) {
    emit('send', recipientEmail.value)
  }
}

defineExpose({
  recipientEmail
})
</script>

<template>
  <div class="email-sender">
    <!-- 未发送状态 -->
    <div v-if="!emailSent" class="send-form">
      <h2 class="section-title">Send Invoice via Email</h2>
      <p class="section-subtitle">Enter the recipient's email address to send the validated XML invoice</p>
      
      <div class="xml-info">
        <div class="info-header">
          <span class="info-title">{{ xmlFilename }}</span>
          <el-button size="small" @click="emit('download')">
            <el-icon><Download /></el-icon>
            Download XML
          </el-button>
        </div>
      </div>

      <div class="email-form">
        <el-form label-width="140px">
          <el-form-item 
            label="Recipient Email"
            :error="recipientEmail && !isValidEmail ? 'Invalid email format' : ''"
          >
            <el-input 
              v-model="recipientEmail" 
              placeholder="user@example.com"
              type="email"
              size="large"
              @blur="validateEmail"
              @input="validateEmail"
            >
              <template #suffix>
                <el-icon v-if="recipientEmail && isValidEmail" style="color: #10b981">
                  <Check />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              size="large"
              :loading="isLoading"
              :disabled="!recipientEmail || !isValidEmail"
              @click="handleSend"
            >
              {{ isLoading ? 'Sending...' : 'Send Invoice' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 发送成功状态 -->
    <div v-else class="success-state">
      <div class="success-icon">
        <el-icon :size="80" color="#10b981">
          <Check />
        </el-icon>
      </div>
      <h2 class="success-title">Invoice Sent Successfully!</h2>
      <p class="success-message">
        The XML invoice has been sent to <strong>{{ recipientEmail }}</strong>
      </p>
      <div class="success-actions">
        <el-button 
          type="primary" 
          size="large"
          :icon="Refresh"
          @click="emit('startOver')"
        >
          Create Another Invoice
        </el-button>
        <el-button 
          size="large"
          @click="emit('download')"
        >
          <el-icon><Download /></el-icon>
          Download XML
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.email-sender {
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
  margin-bottom: 2rem;
}

.xml-info {
  margin: 2rem 0;
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  overflow: hidden;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(16, 185, 129, 0.1);
}

.info-title {
  font-weight: 600;
  color: #10b981;
}

.email-form {
  margin-top: 2rem;
}

:deep(.el-form-item__label) {
  color: #d1d5db !important;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
}

:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #10b981 inset !important;
}

:deep(.el-input__inner) {
  color: #ffffff !important;
}

:deep(.el-form-item.is-error .el-input__wrapper) {
  box-shadow: 0 0 0 1px #f56c6c inset !important;
}

/* 成功状态 */
.success-state {
  text-align: center;
  padding: 3rem 2rem;
}

.success-icon {
  margin-bottom: 2rem;
  animation: scaleIn 0.5s ease;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.success-title {
  font-size: 2rem;
  font-weight: 600;
  color: #10b981;
  margin-bottom: 1rem;
}

.success-message {
  font-size: 1.1rem;
  color: #d1d5db;
  margin-bottom: 2.5rem;
  line-height: 1.6;
}

.success-message strong {
  color: #ffffff;
}

.success-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .success-actions {
    flex-direction: column;
  }

  .success-actions .el-button {
    width: 100%;
  }
}
</style>

