<script setup>
import { RouterView, useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { User, ArrowLeft, Sunny, Moon } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const showNavbar = computed(() => {
  // Show navbar on authenticated pages
  return authStore.isAuthenticated && route.name !== 'login' && route.name !== 'register'
})

const handleLogout = async () => {
  await authStore.logout()
}

const goHome = () => {
  router.push('/')
}

const showBackButton = computed(() => {
  return route.name === 'create' || route.name === 'validate'
})

const pageTitle = computed(() => {
  if (route.name === 'create') return 'E-Invoice Creation'
  if (route.name === 'validate') return 'XML Invoice Validation'
  return 'Dashboard'
})
</script>

<template>
  <div class="app-container">
    <nav v-if="showNavbar" class="navbar">
      <div class="navbar-content">
        <div class="navbar-left">
          <router-link v-if="!showBackButton" to="/" class="navbar-brand">
            <h2>{{ pageTitle }}</h2>
          </router-link>
          <div v-else class="navbar-left-content">
            <el-button 
              text 
              :icon="ArrowLeft" 
              class="back-btn"
              @click="goHome"
            >
              Back to Home
            </el-button>
            <h2 class="page-title">{{ pageTitle }}</h2>
          </div>
        </div>
        <div class="navbar-right">
          <div class="navbar-menu">
            <router-link to="/history" class="nav-link">History</router-link>
            <router-link to="/profile" class="nav-link">Profile</router-link>
            <router-link v-if="authStore.isAdmin" to="/admin" class="nav-link">Admin</router-link>
          </div>
          <el-button 
            text 
            class="theme-toggle-btn"
            :icon="themeStore.theme === 'dark' ? Sunny : Moon"
            @click="themeStore.toggleTheme"
            :title="themeStore.theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
          />
          <div class="user-info">
            <el-icon class="user-icon"><User /></el-icon>
            <span class="username">{{ authStore.user?.username || 'User' }}</span>
          </div>
          <el-button 
            text 
            class="logout-btn"
            @click="handleLogout"
          >
            Logout
          </el-button>
        </div>
      </div>
    </nav>
    <RouterView />
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: var(--bg-navbar);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.navbar-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.navbar-left-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.navbar-brand {
  text-decoration: none;
  color: var(--accent-primary);
  transition: color 0.3s ease;
}

.navbar-brand h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: var(--accent-primary);
  transition: color 0.3s ease;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: var(--accent-primary);
  transition: color 0.3s ease;
}

.back-btn {
  color: var(--text-primary);
  transition: color 0.3s ease;
}

.back-btn:hover {
  color: var(--accent-primary);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.navbar-menu {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-link {
  color: var(--text-primary);
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: var(--accent-primary);
  background-color: var(--bg-hover);
}

.nav-link.router-link-active {
  color: var(--accent-primary);
  background-color: var(--bg-active);
}

.theme-toggle-btn {
  color: var(--text-primary);
  transition: color 0.3s ease;
}

.theme-toggle-btn:hover {
  color: var(--accent-primary);
  background-color: var(--bg-hover);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
  font-size: 0.95rem;
  transition: color 0.3s ease;
}

.user-icon {
  font-size: 1.2rem;
}

.username {
  font-weight: 500;
}

.logout-btn {
  color: var(--text-primary);
  transition: color 0.3s ease;
}

.logout-btn:hover {
  color: var(--accent-primary);
}

:deep(.el-button.is-text) {
  color: var(--text-primary);
  transition: color 0.3s ease, background-color 0.3s ease;
}

:deep(.el-button.is-text:hover) {
  color: var(--accent-primary);
  background-color: var(--bg-hover);
}
</style>
