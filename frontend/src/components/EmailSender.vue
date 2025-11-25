<script setup>
/**
 * EmailSender component for sending validated XML invoices via email.
 * 
 * @component EmailSender
 * @description Allows users to send validated XML invoices to recipients via email.
 * Displays a form for entering recipient email address and handles email sending.
 * Shows success state after email is sent successfully.
 * 
 * @props {string} xmlFilename - XML filename to send
 * @props {boolean} emailSent - Whether email has been sent successfully
 * @props {boolean} isLoading - Whether email is currently being sent
 * 
 * @emits {string} send - Emitted when send button is clicked with recipient email address
 * @emits {void} download - Emitted when download XML button is clicked
 * @emits {void} startOver - Emitted when start over button is clicked
 */
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
    <!-- Not sent state -->
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
                <el-icon v-if="recipientEmail && isValidEmail" style="color: var(--accent-primary)">
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

    <!-- Successfully sent state -->
    <div v-else class="success-state">
      <div class="success-icon">
        <el-icon :size="80" :style="{ color: 'var(--accent-primary)' }">
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

.xml-info {
  margin: 2rem 0;
  border: 1px solid var(--border-accent);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-hover);
  transition: background-color 0.3s ease;
}

.info-title {
  font-weight: 600;
  color: var(--accent-primary);
  transition: color 0.3s ease;
}

.email-form {
  margin-top: 2rem;
}

/* Success state */
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
  color: var(--accent-primary);
  margin-bottom: 1rem;
  transition: color 0.3s ease;
}

.success-message {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin-bottom: 2.5rem;
  line-height: 1.6;
  transition: color 0.3s ease;
}

.success-message strong {
  color: var(--text-primary);
  transition: color 0.3s ease;
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

