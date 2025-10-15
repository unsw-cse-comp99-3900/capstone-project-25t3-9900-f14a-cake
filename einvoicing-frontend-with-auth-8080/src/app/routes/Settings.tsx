import { useSettingsStore } from '../../store/useSettingsStore'
export default function SettingsPage(){
  const { baseUrl, setBaseUrl, token, setToken } = useSettingsStore()
  return (
    <div className="space-y-2 max-w-xl">
      <h2 className="text-xl font-semibold">Settings</h2>
      <label className="block">Base URL</label>
      <input className="input w-full" value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="https://api.example.com" />
      <label className="block">Bearer Token（如使用 Cookie 会话可留空）</label>
      <input className="input w-full" value={token} onChange={e=>setToken(e.target.value)} placeholder="ESS 或后端 Token" />
      <div className="text-gray-500 text-sm">请求 /api/* 会使用此 token；也可以通过 Nginx 反向代理避免 CORS。</div>
    </div>
  )
}
