import { create } from 'zustand'
import { request } from '../lib/request'

type User = { id: string; name: string; role?: string }
type AuthState = {
  user: User | null
  token: string | null
  loading: boolean
  login: (u: string, p: string) => Promise<void>
  loadMe: () => Promise<void>
  logout: () => Promise<void>
  setToken: (t: string | null) => void
}

const TOKEN_KEY = 'auth.token'

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  token: typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null,
  loading: false,
  setToken: (t) => {
    try{
      if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY)
    }catch{}
    set({ token: t })
  },
  login: async (username, password) => {
    set({ loading: true })
    try {
      const { data } = await request.post('/api/auth/login', { username, password }, { withCredentials: true })
      if (data?.accessToken) get().setToken(data.accessToken)
      set({ user: data?.user || null })
    } finally {
      set({ loading: false })
    }
  },
  loadMe: async () => {
    try {
      const { data } = await request.get('/api/auth/me', { withCredentials: true })
      if (data?.user) set({ user: data.user })
    } catch {}
  },
  logout: async () => {
    try { await request.post('/api/auth/logout', {}, { withCredentials: true }) } catch {}
    get().setToken(null); set({ user: null })
  },
}))
