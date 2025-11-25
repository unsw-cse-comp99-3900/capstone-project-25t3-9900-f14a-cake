<script setup>
/**
 * WelcomeView component for application landing page.
 * 
 * @component WelcomeView
 * @description Main landing page displaying application features and navigation options.
 * Shows feature cards for Create Invoice, Validate Invoice, and Invoice History.
 * Includes theme toggle and authentication status display.
 */
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { DocumentAdd, CircleCheck, Clock, Sunny, Moon } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const features = [
  {
    title: 'Create Invoice',
    description: 'Upload PDF or image files to extract invoice data automatically',
    icon: DocumentAdd,
    route: '/create',
    type: 'primary',
    requiresAuth: true
  },
  {
    title: 'Validate Invoice',
    description: 'Validate existing XML invoices against Peppol standards',
    icon: CircleCheck,
    route: '/validate',
    type: 'success',
    requiresAuth: true
  },
  {
    title: 'Invoice History',
    description: 'View and manage your invoice records',
    icon: Clock,
    route: '/history',
    type: 'warning',
    requiresAuth: true
  }
]

const goTo = (route) => {
  router.push(route)
}

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="welcome-page">
    <div class="container">
      <header class="header">
        <el-button 
          v-if="!authStore.isAuthenticated"
          circle
          class="theme-toggle-btn"
          :icon="themeStore.theme === 'dark' ? Sunny : Moon"
          @click="themeStore.toggleTheme"
          :title="themeStore.theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        />
        <h1 class="title">E-Invoice Creator</h1>
        <p class="subtitle">Simplify your invoice management process</p>
        <div v-if="!authStore.isAuthenticated" class="auth-buttons">
          <el-button type="primary" round @click="goToLogin">
            Sign In
          </el-button>
          <el-button round @click="goToRegister">
            Sign Up
          </el-button>
        </div>
      </header>

      <div class="features">
        <div 
          v-for="feature in features" 
          :key="feature.route"
          class="feature-card"
          @click="goTo(feature.route)"
        >
          <div class="feature-icon" :class="feature.type">
            <el-icon :size="32">
              <component :is="feature.icon" />
            </el-icon>
          </div>
          <h2 class="feature-title">{{ feature.title }}</h2>
          <p class="feature-desc">{{ feature.description }}</p>
          <el-button 
            :type="feature.type" 
            class="feature-btn"
            round
          >
            Get Started
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome-page {
  min-height: 100vh;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0rem;
  transition: background 0.3s ease;
}

.container {
  max-width: 1200px;
  width: 100%;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
  position: relative;
}

.theme-toggle-btn {
  position: absolute;
  top: 0;
  right: 0;
  width: 40px;
  height: 40px;
  background: var(--bg-section);
  border: 1px solid transparent;
  color: var(--text-secondary);
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
}

.theme-toggle-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border-accent);
  color: var(--accent-primary);
  transform: scale(1.05);
}

.title {
  font-size: 2.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  letter-spacing: -0.02em;
  transition: color 0.3s ease;
}

.subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  font-weight: 400;
  margin-bottom: 1.5rem;
  transition: color 0.3s ease;
}

.auth-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.feature-card {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: var(--shadow-md);
}


.feature-card:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-accent);
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.feature-icon.primary {
  background: rgba(59, 130, 246, 0.1);
  color: var(--accent-secondary);
}

.feature-icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--accent-primary);
}

.feature-icon.warning {
  background: rgba(251, 191, 36, 0.1);
  color: var(--accent-warning);
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  transition: color 0.3s ease;
}

.feature-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 1.5rem;
  flex: 1;
  transition: color 0.3s ease;
}

.feature-btn {
  min-width: 140px;
}

@media (max-width: 1024px) {
  .features {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .title {
    font-size: 2rem;
  }

  .features {
    grid-template-columns: 1fr;
  }

  .theme-toggle-btn {
    width: 36px;
    height: 36px;
    top: -0.5rem;
    right: -0.5rem;
  }
}
</style>
