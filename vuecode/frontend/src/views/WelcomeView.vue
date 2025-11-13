<script setup>
import { useRouter } from 'vue-router'
import { DocumentAdd, CircleCheck } from '@element-plus/icons-vue'

const router = useRouter()

const features = [
  {
    title: 'Create Invoice',
    description: 'Upload PDF or image files to extract invoice data automatically',
    icon: DocumentAdd,
    route: '/create',
    type: 'primary'
  },
  {
    title: 'Validate Invoice',
    description: 'Validate existing XML invoices against Peppol standards',
    icon: CircleCheck,
    route: '/validate',
    type: 'success'
  }
]

const goTo = (route) => {
  router.push(route)
}
</script>

<template>
  <div class="welcome-page">
    <div class="container">
      <header class="header">
        <h1 class="title">E-Invoice Creator</h1>
        <p class="subtitle">Simplify your invoice management process</p>
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
  background: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.container {
  max-width: 900px;
  width: 100%;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
}

.title {
  font-size: 2.5rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 0.75rem;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 1.1rem;
  color: #9ca3af;
  font-weight: 400;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(16, 185, 129, 0.3);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(16, 185, 129, 0.15);
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
  color: #60a5fa;
}

.feature-icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 0.75rem;
}

.feature-desc {
  font-size: 1.05rem;
  color: #d1d5db;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  flex: 1;
}

.feature-btn {
  min-width: 140px;
}

@media (max-width: 640px) {
  .title {
    font-size: 2rem;
  }

  .features {
    grid-template-columns: 1fr;
  }
}
</style>
