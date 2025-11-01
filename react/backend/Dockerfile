# 1. 使用一个官方的 Python 基础镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制所有后端代码到镜像中
COPY . .

# 5. 声明容器将监听的端口
EXPOSE 5001

# 6. 启动 Flask 程序的命令
# "0.0.0.0" 允许从容器外部访问
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]