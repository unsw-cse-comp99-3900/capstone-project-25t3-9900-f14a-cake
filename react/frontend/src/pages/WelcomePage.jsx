import React from 'react';
import { useNavigate } from 'react-router-dom';
import './WelcomePage.css'; // 我们为这个页面创建单独的 CSS

const WelcomePage = () => {
  const navigate = useNavigate(); // 用于页面跳转的 hook

  return (
    <div className="welcome-container">
      {/* 标题: 居中偏上 */}
      <h1 className="welcome-title">
        Welcome to e-invoice creater!
      </h1>

      {/* 按钮容器 */}
      <div className="button-wrapper">
        
        {/* 创建按钮 */}
        <div className="action-box">
          <p>Don't have an invoice? Create one now.</p>
          <button 
            className="action-button create-button"
            onClick={() => navigate('/create')}
          >
            Create Invoice
          </button>
        </div>

        {/* 验证按钮 */}
        <div className="action-box">
          <p>Already have an XML invoice? Validate it.</p>
          <button 
            className="action-button validate-button"
            onClick={() => navigate('/validate')}
          >
            Validate Invoice
          </button>
        </div>

      </div>
    </div>
  );
};

export default WelcomePage;