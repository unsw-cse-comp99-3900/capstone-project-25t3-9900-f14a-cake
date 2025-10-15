import { ReactNode, useEffect } from 'react'
import { useAuth } from '../store/auth'
import { useLocation, useNavigate } from 'react-router-dom'

export function Protected({ children }: { children: ReactNode }){
  const { user, loadMe } = useAuth()
  const loc = useLocation()
  const nav = useNavigate()

  useEffect(()=>{ if(!user) loadMe() },[])
  useEffect(()=>{
    if(!user){
      const to = encodeURIComponent(loc.pathname + loc.search)
      nav(`/login?redirect=${to}`, { replace: true })
    }
  },[user, loc.pathname])
  return <>{user ? children : null}</>
}
