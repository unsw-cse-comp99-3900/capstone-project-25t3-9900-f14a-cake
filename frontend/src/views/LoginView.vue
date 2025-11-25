<script setup>
/**
 * LoginView component for user authentication.
 * 
 * @component LoginView
 * @description Provides login form for user authentication.
 * Validates email and password, handles login errors, and redirects authenticated users.
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = ref({
  email: '',
  password: ''
})

const loginRules = {
  email: [
    { required: true, message: 'Please enter your email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email address', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please enter your password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
  ]
}

const formRef = ref(null)
const isLoading = ref(false)

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      isLoading.value = true
      try {
        const result = await authStore.login(loginForm.value.email, loginForm.value.password)
        if (result.success) {
          // Redirect to home page
          router.push('/')
        }
      } catch (error) {
        console.error('Login error:', error)
      } finally {
        isLoading.value = false
      }
    }
  })
}

const goToRegister = () => {
  router.push('/register')
}

const goToForgotPassword = () => {
  router.push({
    path: '/forgot-password',
    query: loginForm.value.email ? { email: loginForm.value.email } : {}
  })
}

const goBack = () => {
  router.push('/')
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <el-button 
            text 
            :icon="ArrowLeft" 
            class="back-btn"
            @click="goBack"
          >
            Back
          </el-button>
          <h1 class="login-title">Welcome Back</h1>
          <p class="login-subtitle">Sign in to continue to E-Invoice Creator</p>
        </div>

        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="email">
            <el-input
              v-model="loginForm.email"
              type="email"
              placeholder="Email"
              size="large"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="Password"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
            <div class="forgot-password-link">
              <el-button text type="primary" @click="goToForgotPassword">
                Forgot Password?
              </el-button>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="isLoading"
              @click="handleLogin"
            >
              {{ isLoading ? 'Signing in...' : 'Sign In' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <p class="register-link">
            Don't have an account?
            <el-button text type="primary" @click="goToRegister">
              Sign Up
            </el-button>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  transition: background 0.3s ease;
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.login-card {
  background: var(--bg-section);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 2.5rem;
  box-shadow: var(--shadow-md);
  transition: background-color 0.3s ease, border-color 0.3s ease;
  position: relative;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.back-btn {
  position: absolute;
  left: 0rem;
  top: 1rem;
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

.login-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
  transition: color 0.3s ease;
}

.login-subtitle {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s ease;
}

.login-form {
  margin-top: 2rem;
}

.login-btn {
  width: 100%;
  margin-top: 0.5rem;
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
}

.register-link {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
  transition: color 0.3s ease;
}

.login-footer :deep(.el-button--primary.is-text) {
  color: var(--link-button-color);
  padding: 0 0.25rem;
  margin-left: 0;
  transition: color 0.3s ease;
}

.login-footer :deep(.el-button--primary.is-text:hover) {
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

.forgot-password-link {
  margin-top: 0.5rem;
  text-align: right;
}

.forgot-password-link :deep(.el-button--primary.is-text) {
  color: var(--link-button-color);
  padding: 0;
  font-size: 0.85rem;
  transition: color 0.3s ease;
}

.forgot-password-link :deep(.el-button--primary.is-text:hover) {
  color: var(--link-button-hover-color);
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

