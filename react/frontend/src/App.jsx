import React from 'react'
import { Routes, Route } from 'react-router-dom'
import WelcomePage from './pages/WelcomePage'
import CreatePage from './pages/CreatePage'
import ValidatePage from './pages/ValidatePage'

function App() {
  return (
    <Routes>
      {/* 根路径 ("/") 显示欢迎页面 */}
      <Route path="/" element={<WelcomePage />} />
      
      {/* "/create" 路径显示创建页面 */}
      <Route path="/create" element={<CreatePage />} />
      
      {/* "/validate" 路径显示验证页面 */}
      <Route path="/validate" element={<ValidatePage />} />
    </Routes>
  )
}

export default App