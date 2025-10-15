import { useEffect, useState } from 'react'
import { useAuth } from '../../store/auth'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'

export default function LoginPage(){
  const [search] = useSearchParams()
  const redirect = search.get('redirect') || '/'
  const nav = useNavigate()
  const { user, login, loading } = useAuth()
  const [form, setForm] = useState({ username:'', password:'' })
  const [err, setErr] = useState('')

  useEffect(()=>{ if(user) nav(redirect, { replace: true }) }, [user])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErr('')
    try { await login(form.username.trim(), form.password) }
    catch (e:any){ setErr(e?.message || '登录失败') }
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-semibold mb-4">登录</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input className="input w-full" placeholder="用户名" value={form.username} onChange={e=>setForm({...form, username:e.target.value})}/>
        <input className="input w-full" type="password" placeholder="密码" value={form.password} onChange={e=>setForm({...form, password:e.target.value})}/>
        <button className="btn w-full" disabled={loading}>{loading ? '登录中...' : '登录'}</button>
        {err && <div className="text-red-600 text-sm">{err}</div>}
      </form>
      <div className="text-sm text-gray-500 mt-3">演示账号（MSW）：alice / secret</div>
      <div className="mt-4"><Link to="/">返回首页</Link></div>
    </div>
  )
}
