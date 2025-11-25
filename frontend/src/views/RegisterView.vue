<script setup>
/**
 * RegisterView component for user registration.
 * 
 * @component RegisterView
 * @description Provides registration form with email verification.
 * Validates username (max 12 chars), email, password, and verification code.
 * Sends verification code via email before allowing registration.
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock, Message, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  verificationCode: ''
})

const countdown = ref(0)
const isSendingCode = ref(false)
let countdownTimer = null

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.value.password) {
    callback(new Error('Passwords do not match'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: 'Please enter a username', trigger: 'blur' },
    { min: 3, message: 'Username must be at least 3 characters', trigger: 'blur' },
    { max: 12, message: 'Username must be 12 characters or less', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: 'Username can only contain letters, numbers, underscores and hyphens',
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email address', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter a password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
    { max: 128, message: 'Password must be less than 128 characters', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm your password', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  verificationCode: [
    { required: true, message: 'Please enter the verification code', trigger: 'blur' },
    { len: 6, message: 'Verification code must be 6 digits', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: 'Verification code must be 6 digits', trigger: 'blur' }
  ]
}

const canSendCode = computed(() => {
  return countdown.value === 0 && !isSendingCode.value && registerForm.value.email && 
         /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.value.email)
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
  if (!registerForm.value.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.value.email)) {
    ElMessage.warning('Please enter a valid email address')
    return
  }

  isSendingCode.value = true
  try {
    const result = await authStore.sendVerificationCode(registerForm.value.email)
    if (result.success) {
      startCountdown()
    }
  } catch (error) {
    console.error('Send code error:', error)
  } finally {
    isSendingCode.value = false
  }
}

const handleRegister = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      isLoading.value = true
      try {
        const result = await authStore.register(
          registerForm.value.username,
          registerForm.value.email,
          registerForm.value.password,
          registerForm.value.verificationCode
        )
        if (result.success) {
          // Clear countdown
          if (countdownTimer) {
            clearInterval(countdownTimer)
            countdownTimer = null
          }
          // Redirect to home page
          router.push('/')
        }
      } catch (error) {
        console.error('Registration error:', error)
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
  router.push('/')
}
</script>

<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-card">
        <div class="register-header">
          <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack">
            Back
          </el-button>
          <h1 class="register-title">Create Account</h1>
          <p class="register-subtitle">Sign up to get started with E-Invoice Creator</p>
        </div>

        <el-form ref="formRef" :model="registerForm" :rules="registerRules" class="register-form"
          @submit.prevent="handleRegister">
          <el-form-item prop="username">
            <el-input v-model="registerForm.username" placeholder="Username" size="large" :prefix-icon="User"
              clearable />
          </el-form-item>

          <el-form-item prop="email">
            <el-input 
              v-model="registerForm.email" 
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
                v-model="registerForm.verificationCode" 
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
            <el-input v-model="registerForm.password" type="password" placeholder="Password" size="large"
              :prefix-icon="Lock" show-password />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input v-model="registerForm.confirmPassword" type="password" placeholder="Confirm Password" size="large"
              :prefix-icon="Lock" show-password @keyup.enter="handleRegister" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" class="register-btn" :loading="isLoading" @click="handleRegister">
              {{ isLoading ? 'Creating account...' : 'Sign Up' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="register-footer">
          <p class="login-link">
            Already have an account?
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
.register-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  transition: background 0.3s ease;
}

.register-container {
  width: 100%;
  max-width: 420px;
}

.register-card {
  background: var(--bg-section);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 2.5rem;
  box-shadow: var(--shadow-md);
  position: relative;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.register-header {
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

.register-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
  transition: color 0.3s ease;
}

.register-subtitle {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s ease;
}

.register-form {
  margin-top: 2rem;
}

.register-btn {
  width: 100%;
  margin-top: 0.5rem;
}

.register-footer {
  margin-top: 2rem;
  text-align: center;
}

.login-link {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
  transition: color 0.3s ease;
}

.register-footer :deep(.el-button--primary.is-text) {
  color: var(--link-button-color);
  padding: 0 0.25rem;
  margin-left: 0;
  transition: color 0.3s ease;
}

.register-footer :deep(.el-button--primary.is-text:hover) {
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
