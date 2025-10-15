import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './routes/Dashboard'
import CreatePage from './routes/Create'
import ValidatePage from './routes/ValidateESS'
import SendPage from './routes/Send'
import SettingsPage from './routes/Settings'
import DocsPage from './routes/Docs'
import LoginPage from './routes/Login'
import { Protected } from './Protected'
import { useAuth } from '../store/auth'

export default function App(){
  const tabs = [
    {to:'/',label:'Dashboard'},
    {to:'/create',label:'Create'},
    {to:'/validate',label:'Validate (ESS + Schema)'},
    {to:'/send',label:'Send'},
    {to:'/settings',label:'Settings'},
    {to:'/docs',label:'Docs'},
  ]
  const { user, logout } = useAuth()
  return (
    <BrowserRouter>
      <div className="min-h-screen grid grid-rows-[auto,1fr]">
        <nav className="border-b px-4 py-2 flex gap-2 flex-wrap items-center">
          {tabs.map(t=>(
            <NavLink key={t.to} to={t.to} className={({isActive})=>`px-3 py-1 rounded hover:bg-gray-100 ${isActive?'bg-gray-200 font-medium':''}`}>{t.label}</NavLink>
          ))}
          <div className="ml-auto flex items-center gap-2">
            {user ? (<>
              <span className="text-sm text-gray-600">Hi, {user.name}</span>
              <button className="btn" onClick={logout}>退出</button>
            </>) : (
              <NavLink to="/login" className="px-3 py-1 rounded hover:bg-gray-100">登录</NavLink>
            )}
          </div>
        </nav>
        <main className="p-4 max-w-7xl mx-auto w-full">
          <Routes>
            <Route path="/login" element={<LoginPage/>} />
            <Route path="/" element={<Protected><Dashboard/></Protected>} />
            <Route path="/create" element={<Protected><CreatePage/></Protected>} />
            <Route path="/validate" element={<Protected><ValidatePage/></Protected>} />
            <Route path="/send" element={<Protected><SendPage/></Protected>} />
            <Route path="/settings" element={<Protected><SettingsPage/></Protected>} />
            <Route path="/docs" element={<Protected><DocsPage/></Protected>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
