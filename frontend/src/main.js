import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import './styles/themes.css'
import './styles/element-plus-theme.css'

const app = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// Initialize stores
const authStore = useAuthStore()
authStore.init()

const themeStore = useThemeStore()
// Theme is automatically initialized in the store

app.mount('#app')
