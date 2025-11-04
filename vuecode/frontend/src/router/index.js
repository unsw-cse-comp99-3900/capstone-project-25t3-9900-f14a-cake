import { createRouter, createWebHistory } from 'vue-router'
import WelcomeView from '../views/WelcomeView.vue'
import CreateInvoiceView from '../views/CreateInvoiceView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'welcome',
      component: WelcomeView,
    },
    {
      path: '/create',
      name: 'create',
      component: CreateInvoiceView,
    },
    {
      path: '/validate',
      name: 'validate',
      component: () => import('../views/ValidateView.vue'),
    },
  ],
})

export default router
