# E-invoicing Frontend (Auth) — Final

包含：登录/鉴权、Create（表单/CSV/DB/OCR→UBL）、Validate（ESS+Schema，导出 JSON/HTML/PDF）、Send（Email/SFTP/PEPPOL），Docker 端口 8080。

## 快速开始（本地模拟 API）
```bash
docker compose up --build -d
open http://localhost:8080/login
# 账号：alice / secret
```

## 与真实后端联调
1. 复制 `.env.example` 为 `.env` 并填写：
   ```env
   API_BASE=https://your-backend.example.com
   ```
2. 运行：
   ```bash
   docker compose -f docker-compose.proxy.yml up --build -d
   ```

## 路由
- /login（登录）
- /（Dashboard）
- /create（生成 UBL：表单/CSV/Excel/SQLite/OCR）
- /validate（ESS+Schema 校验，导出 JSON/HTML/PDF）
- /send（Email/SFTP/PEPPOL 发送示例）
- /settings（BaseURL/Token 设置——可不填，推荐用反代）
- /docs（接口说明）

## 说明
- 构建：`npm run build`（Vite + TypeScript）
- MSW：仅开发环境启用，Docker 构建出的静态站点使用真实接口或 Nginx 反代接口。
- 认证：支持 Bearer（localStorage）与 Cookie 会话（需 withCredentials + 反代允许 Credentials）。


> 此包内置 **Nginx Mock API**，无需后端即可登录与校验/发送演示。若要对接真实后端，可改用 docker-compose.proxy.yml。
