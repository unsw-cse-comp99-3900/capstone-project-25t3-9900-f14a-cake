<script setup>
/**
 * ForgotPasswordView component for password reset functionality.
 * 
 * @component ForgotPasswordView
 * @description Allows users to reset their password via email verification.
 * Sends verification code to user's email and validates code before allowing password reset.
 * Supports password confirmation validation.
 */
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Message, Lock, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const resetForm = ref({
  email: '',
  verificationCode: '',
  password: '',
  confirmPassword: ''
})

const countdown = ref(0)
const isSendingCode = ref(false)
let countdownTimer = null

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== resetForm.value.password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

const resetRules = {
  email: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email address', trigger: 'blur' }
  ],
  verificationCode: [
    { required: true, message: 'Please enter the verification code', trigger: 'blur' },
    { len: 6, message: 'Verification code must be 6 digits', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: 'Verification code must be 6 digits', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter a new password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
    { max: 128, message: 'Password must be less than 128 characters', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm your password', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const canSendCode = computed(() => {
  return countdown.value === 0 && !isSendingCode.value && resetForm.value.email && 
         /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(resetForm.value.email)
})

const sendCodeButtonText = computed(() => {
  if (isSendingCode.value) {
    return 'Sending...'
  }
  if (countdown.value > 0) {
    return `Resend (${countdown.value}s)`
  }
  return 'Send Code'
})

const formRef = ref(null)
const isLoading = ref(false)

const startCountdown = () => {
  countdown.value = 60
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

const handleSendCode = async () => {
  if (!canSendCode.value) return

  // Validate email first
  if (!resetForm.value.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(resetForm.value.email)) {
    ElMessage.warning('Please enter a valid email address')
    return
  }

  isSendingCode.value = true
  try {
    const result = await authStore.sendVerificationCode(resetForm.value.email)
    if (result.success) {
      startCountdown()
    }
  } catch (error) {
    console.error('Send code error:', error)
  } finally {
    isSendingCode.value = false
  }
}

const handleResetPassword = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      isLoading.value = true
      try {
        const result = await authStore.resetPassword(
          resetForm.value.email,
          resetForm.value.verificationCode,
          resetForm.value.password
        )
        if (result.success) {
          // Clear countdown
          if (countdownTimer) {
            clearInterval(countdownTimer)
            countdownTimer = null
          }
          // Redirect to login page
          router.push('/login')
        }
      } catch (error) {
        console.error('Reset password error:', error)
      } finally {
        isLoading.value = false
      }
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}

const goBack = () => {
  router.push('/login')
}

onMounted(() => {
  // Auto-fill email from query parameter if provided
  if (route.query.email) {
    resetForm.value.email = route.query.email
  }
})

onBeforeUnmount(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<template>
  <div class="forgot-password-page">
    <div class="forgot-password-container">
      <div class="forgot-password-card">
        <div class="forgot-password-header">
          <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack">
            Back
          </el-button>
          <h1 class="forgot-password-title">Reset Password</h1>
          <p class="forgot-password-subtitle">Enter your email and verification code to reset your password</p>
        </div>

        <el-form ref="formRef" :model="resetForm" :rules="resetRules" class="forgot-password-form"
          @submit.prevent="handleResetPassword">
          <el-form-item prop="email">
            <el-input 
              v-model="resetForm.email" 
              type="email" 
              placeholder="Email" 
              size="large" 
              :prefix-icon="Message"
              clearable 
            />
          </el-form-item>

          <el-form-item prop="verificationCode">
            <div style="display: flex; gap: 0.5rem;">
              <el-input 
                v-model="resetForm.verificationCode" 
                placeholder="Enter 6-digit verification code" 
                size="large"
                :prefix-icon="Message"
                maxlength="6"
                style="flex: 1;"
              />
              <el-button 
                type="primary" 
                size="large"
                :disabled="!canSendCode"
                :loading="isSendingCode"
                @click="handleSendCode"
              >
                {{ sendCodeButtonText }}
              </el-button>
            </div>
            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">
              A verification code will be sent to your email.
            </div>
          </el-form-item>

          <el-form-item prop="password">
            <el-input 
              v-model="resetForm.password" 
              type="password" 
              placeholder="New Password" 
              size="large"
              :prefix-icon="Lock" 
              show-password 
              autocomplete="new-password"
            />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input 
              v-model="resetForm.confirmPassword" 
              type="password" 
              placeholder="Confirm New Password" 
              size="large"
              :prefix-icon="Lock" 
              show-password 
              autocomplete="new-password"
              @keyup.enter="handleResetPassword" 
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" class="reset-btn" :loading="isLoading" @click="handleResetPassword">
              {{ isLoading ? 'Resetting password...' : 'Reset Password' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="forgot-password-footer">
          <p class="login-link">
            Remember your password?
            <el-button text type="primary" @click="goToLogin">
              Sign In
            </el-button>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forgot-password-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  transition: background 0.3s ease;
}

.forgot-password-container {
  width: 100%;
  max-width: 420px;
}

.forgot-password-card {
  background: var(--bg-section);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 2.5rem;
  box-shadow: var(--shadow-md);
  position: relative;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.forgot-password-header {
  text-align: center;
  margin-bottom: 2rem;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 0;
  color: var(--text-secondary);
  transition: color 0.3s ease;
}

.back-btn:hover {
  color: var(--accent-primary);
}

:root[data-theme="dark"] .back-btn,
:root[data-theme="dark"] .back-btn:focus,
:root[data-theme="dark"] .back-btn:active {
  background-color: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
}

:root[data-theme="dark"] .back-btn:hover {
  background-color: transparent !important;
  border-color: transparent !important;
}

.forgot-password-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
  transition: color 0.3s ease;
}

.forgot-password-subtitle {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s ease;
}

.forgot-password-form {
  margin-top: 2rem;
}

.reset-btn {
  width: 100%;
  margin-top: 0.5rem;
}

.forgot-password-footer {
  margin-top: 2rem;
  text-align: center;
}

.login-link {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
  transition: color 0.3s ease;
}

.forgot-password-footer :deep(.el-button--primary.is-text) {
  color: var(--link-button-color);
  padding: 0 0.25rem;
  margin-left: 0;
  transition: color 0.3s ease;
}

.forgot-password-footer :deep(.el-button--primary.is-text:hover) {
  color: var(--link-button-hover-color);
  padding: 0 0.25rem;
}

/* Element Plus styles - ensure they work correctly in both themes */
:deep(.el-input__wrapper) {
  background-color: var(--bg-input) !important;
  box-shadow: 0 0 0 1px var(--border-secondary) inset !important;
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

:deep(.el-input__wrapper:hover),
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--border-focus) inset !important;
}

:deep(.el-input__inner) {
  color: var(--text-primary) !important;
  transition: color 0.3s ease;
}

:deep(.el-form-item__label) {
  color: var(--text-primary) !important;
  font-weight: 500;
  transition: color 0.3s ease;
}

:deep(.el-form-item.is-error .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--accent-danger) inset !important;
}

:deep(.el-form-item__error) {
  color: var(--accent-danger);
}

/* Fix browser autofill background color */
:deep(.el-input__inner:-webkit-autofill),
:deep(.el-input__inner:-webkit-autofill:hover),
:deep(.el-input__inner:-webkit-autofill:focus),
:deep(.el-input__inner:-webkit-autofill:active) {
  -webkit-text-fill-color: var(--text-primary) !important;
  transition: background-color 5000s ease-in-out 0s;
  caret-color: var(--text-primary) !important;
}
</style>

