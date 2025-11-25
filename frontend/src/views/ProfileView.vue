<script setup>
/**
 * ProfileView component for user profile management.
 * 
 * @component ProfileView
 * @description Allows users to update their profile information and password.
 * Supports username (max 12 chars), email updates with verification, and password changes.
 * Displays current user information and handles form validation.
 */
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/axios'

const router = useRouter()
const authStore = useAuthStore()

const profileForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  verificationCode: ''
})

const originalEmail = ref('')
const countdown = ref(0)
const isSendingCode = ref(false)
let countdownTimer = null

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const profileRules = {
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
  verificationCode: [
    { 
      validator: (rule, value, callback) => {
        // Only required if email is changed
        if (isEmailChanged.value && (!value || value.trim() === '')) {
          callback(new Error('Verification code is required when changing email'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'change']
    },
    {
      validator: (rule, value, callback) => {
        // Only validate format if email is changed and code is provided
        if (isEmailChanged.value && value && (value.length !== 6 || !/^\d{6}$/.test(value))) {
          callback(new Error('Verification code must be 6 digits'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'change']
    }
  ]
}

const isEmailChanged = computed(() => {
  return profileForm.value.email !== originalEmail.value
})

const canSendCode = computed(() => {
  return countdown.value === 0 && !isSendingCode.value && profileForm.value.email && 
         /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileForm.value.email) &&
         isEmailChanged.value
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
  if (!profileForm.value.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileForm.value.email)) {
    ElMessage.warning('Please enter a valid email address')
    return
  }

  if (!isEmailChanged.value) {
    ElMessage.warning('Email has not been changed')
    return
  }

  isSendingCode.value = true
  try {
    const result = await authStore.sendVerificationCode(profileForm.value.email)
    if (result.success) {
      startCountdown()
    }
  } catch (error) {
    console.error('Send code error:', error)
  } finally {
    isSendingCode.value = false
  }
}

const passwordRules = {
  currentPassword: [
    {
      validator: (rule, value, callback) => {
        // On blur: if empty, clear error; if has value, validate
        if (!value || value.trim() === '') {
          callback()
        } else {
          callback()
        }
      },
      trigger: 'blur'
    },
    {
      validator: (rule, value, callback) => {
        // On change or submit: validate required
        if (!value || value.trim() === '') {
          callback(new Error('Please enter your current password'))
        } else {
          callback()
        }
      },
      trigger: ['change', 'submit']
    }
  ],
  newPassword: [
    {
      validator: (rule, value, callback) => {
        // On blur: if empty, clear error; if has value, validate
        if (!value || value.trim() === '') {
          callback()
        } else if (value.length < 6) {
          callback(new Error('Password must be at least 6 characters'))
        } else if (value.length > 128) {
          callback(new Error('Password must be less than 128 characters'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    },
    {
      validator: (rule, value, callback) => {
        // On change or submit: validate required and rules
        if (!value || value.trim() === '') {
          callback(new Error('Please enter a new password'))
        } else if (value.length < 6) {
          callback(new Error('Password must be at least 6 characters'))
        } else if (value.length > 128) {
          callback(new Error('Password must be less than 128 characters'))
        } else {
          callback()
        }
      },
      trigger: ['change', 'submit']
    }
  ],
  confirmPassword: [
    {
      validator: (rule, value, callback) => {
        // On blur: if empty, clear error; if has value, validate
        if (!value || value.trim() === '') {
          callback()
        } else if (value !== passwordForm.value.newPassword) {
          callback(new Error('Passwords do not match'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    },
    {
      validator: (rule, value, callback) => {
        // On change or submit: validate required and match
        if (!value || value.trim() === '') {
          callback(new Error('Please confirm your new password'))
        } else if (value !== passwordForm.value.newPassword) {
          callback(new Error('Passwords do not match'))
        } else {
          callback()
        }
      },
      trigger: ['change', 'submit']
    }
  ]
}

const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const isLoading = ref(false)
const isPasswordLoading = ref(false)
const activeTab = ref('profile')

const loadProfile = async () => {
  try {
    isLoading.value = true
    await authStore.fetchProfile()
    
    if (authStore.user) {
      originalEmail.value = authStore.user.email || ''
      profileForm.value = {
        username: authStore.user.username || '',
        email: authStore.user.email || '',
        password: '',
        confirmPassword: '',
        verificationCode: ''
      }
      // Clear countdown if exists
      if (countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
      countdown.value = 0
    }
  } catch (error) {
    console.error('Failed to load profile:', error)
  } finally {
    isLoading.value = false
  }
}

const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return
  
  await profileFormRef.value.validate(async (valid) => {
    if (valid) {
      isLoading.value = true
      try {
        const updateData = {
          username: profileForm.value.username,
          email: profileForm.value.email
        }
        
        // If email is changed, include verification code
        if (isEmailChanged.value) {
          if (!profileForm.value.verificationCode || profileForm.value.verificationCode.trim() === '') {
            ElMessage.error('Verification code is required when changing email')
            isLoading.value = false
            return
          }
          updateData.verification_code = profileForm.value.verificationCode.trim()
        }
        
        await authStore.updateProfile(updateData)
        
        // Update original email after successful update
        originalEmail.value = profileForm.value.email
        
        // Reset fields
        profileForm.value.password = ''
        profileForm.value.confirmPassword = ''
        profileForm.value.verificationCode = ''
        
        // Clear countdown
        if (countdownTimer) {
          clearInterval(countdownTimer)
          countdownTimer = null
        }
        countdown.value = 0
      } catch (error) {
        console.error('Update profile error:', error)
      } finally {
        isLoading.value = false
      }
    }
  })
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      isPasswordLoading.value = true
      try {
        // First verify current password by trying to login
        const verifyResponse = await api.post('/auth/login', {
          email: authStore.user.email,
          password: passwordForm.value.currentPassword
        })
        
        if (!verifyResponse.data || verifyResponse.data.error) {
          ElMessage.error('Current password is incorrect')
          return
        }
        
        // Update password
        await authStore.updateProfile({
          password: passwordForm.value.newPassword
        })
        
        // Reset password form
        passwordForm.value = {
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }
        passwordFormRef.value.clearValidate()
      } catch (error) {
        if (error.response?.status === 401) {
          ElMessage.error('Current password is incorrect')
        } else {
          ElMessage.error('Failed to change password')
        }
        console.error('Change password error:', error)
      } finally {
        isPasswordLoading.value = false
      }
    }
  })
}

onMounted(() => {
  loadProfile()
})

onBeforeUnmount(() => {
  // Clear countdown timer when component is unmounted
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="profile-card">
        <div class="profile-header">
          <h1 class="page-title">My Profile</h1>
          <p class="page-subtitle">Manage your account information and password</p>
        </div>

        <el-tabs v-model="activeTab" class="profile-tabs">
          <!-- Profile Information Tab -->
          <el-tab-pane label="Profile Information" name="profile">
            <el-form
              ref="profileFormRef"
              :model="profileForm"
              :rules="profileRules"
              class="profile-form"
              label-width="140px"
            >
              <el-form-item label="Username" prop="username">
                <el-input
                  v-model="profileForm.username"
                  placeholder="Username"
                  size="large"
                  :prefix-icon="User"
                  clearable
                />
              </el-form-item>

              <el-form-item label="Email" prop="email">
                <el-input
                  v-model="profileForm.email"
                  type="email"
                  placeholder="Email"
                  size="large"
                  :prefix-icon="Message"
                  clearable
                />
              </el-form-item>

              <el-form-item 
                v-if="isEmailChanged" 
                label="Verification Code" 
                prop="verificationCode"
              >
                <div style="display: flex; gap: 0.5rem;">
                  <el-input 
                    v-model="profileForm.verificationCode" 
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
                  A verification code will be sent to your new email address.
                </div>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="isLoading"
                  @click="handleUpdateProfile"
                >
                  {{ isLoading ? 'Updating...' : 'Update Profile' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- Change Password Tab -->
          <el-tab-pane label="Change Password" name="password">
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              class="password-form"
              label-width="160px"
            >
              <el-form-item label="Current Password" prop="currentPassword">
                <el-input
                  v-model="passwordForm.currentPassword"
                  type="password"
                  placeholder="Enter your current password"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item label="New Password" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  placeholder="Enter your new password"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item label="Confirm Password" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  placeholder="Confirm your new password"
                  size="large"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="isPasswordLoading"
                  @click="handleChangePassword"
                >
                  {{ isPasswordLoading ? 'Changing...' : 'Change Password' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  padding: 2rem;
  transition: background 0.3s ease;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  background: var(--bg-section);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 2.5rem;
  box-shadow: var(--shadow-md);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.profile-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
  transition: color 0.3s ease;
}

.page-subtitle {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s ease;
}

.profile-tabs {
  margin-top: 2rem;
}

.profile-form,
.password-form {
  margin-top: 1.5rem;
}

:deep(.el-tabs__header) {
  margin-bottom: 2rem;
}

:deep(.el-tabs__nav-wrap::after) {
  background-color: var(--border-primary);
  transition: background-color 0.3s ease;
}

:deep(.el-tabs__item) {
  color: var(--text-secondary);
  font-weight: 500;
  transition: color 0.3s ease;
}

:deep(.el-tabs__item.is-active) {
  color: var(--accent-primary);
}

:deep(.el-tabs__active-bar) {
  background-color: var(--accent-primary);
  transition: background-color 0.3s ease;
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

