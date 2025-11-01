import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 允许 Docker 容器内的 vite 进程被外部访问
    host: '0.0.0.0', 
    port: 5173,
  }
})
