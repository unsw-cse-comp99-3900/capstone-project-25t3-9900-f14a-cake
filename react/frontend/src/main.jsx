import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom' // 导入
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* 用 BrowserRouter 包裹 App */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)