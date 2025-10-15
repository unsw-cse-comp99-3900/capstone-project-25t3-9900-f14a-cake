import axios, { AxiosRequestHeaders } from 'axios'
import { useSettingsStore } from '../store/useSettingsStore'
import { useAuth } from '../store/auth'
export const request = axios.create({ timeout: 20000 })

request.interceptors.request.use((config)=>{
  const { baseUrl } = useSettingsStore.getState()
  const { token } = useAuth.getState()
  if (config.url?.startsWith('/')) config.baseURL = baseUrl || ''
  const headers = (config.headers || {}) as AxiosRequestHeaders
  if (token) headers['Authorization'] = `Bearer ${token}`
  config.headers = headers
  return config
})

request.interceptors.response.use(
  (res)=>res,
  (err)=>{
    if (err?.response?.status === 401) {
      const { logout } = useAuth.getState()
      logout()
      const target = encodeURIComponent(window.location.pathname + window.location.search)
      if (!window.location.pathname.startsWith('/login')) window.location.href = `/login?redirect=${target}`
    }
    return Promise.reject(err)
  }
)
