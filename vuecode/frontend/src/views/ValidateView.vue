<script setup>
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()

const goBack = () => {
  router.push('/')
}
</script>

<template>
  <div class="validate-container">
    <div class="header">
      <div class="header-content">
        <h1 class="header-title">XML Invoice Validation</h1>
        <el-button 
          @click="goBack" 
          class="back-button"
          :icon="ArrowLeft"
        >
          Back to Home
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="placeholder">
        <h2>Validation Feature</h2>
        <p>This feature is coming soon...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.validate-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0f1a 0%, #1a2332 100%);
}

.header {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(16, 185, 129, 0.2);
  padding: 1.5rem 2rem;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 2rem;
  font-weight: 700;
  color: #10b981;
  margin: 0;
  text-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

.back-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: #10b981;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 3rem 2rem;
}

.placeholder {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  padding: 4rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
}

.placeholder h2 {
  font-size: 2rem;
  color: #ffffff;
  margin-bottom: 1rem;
}

.placeholder p {
  font-size: 1.2rem;
  color: #9ca3af;
}
</style>

