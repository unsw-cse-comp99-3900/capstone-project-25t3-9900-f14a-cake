# --- 阶段 1: 构建 (Build) ---
# 使用一个 Node.js 镜像作为构建环境
FROM node:18-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装所有依赖
RUN npm install

# 复制所有前端源代码
COPY . .

# 构建生产版本
RUN npm run build

# --- 阶段 2: 运行 (Serve) ---
# 使用一个轻量级的 nginx 镜像来提供静态文件
FROM nginx:1.23-alpine

# 从 "build" 阶段复制构建好的文件到 nginx 的 web 根目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制自定义的 nginx 配置 (如果需要的话, 暂时省略)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口 (nginx 默认端口)
EXPOSE 80