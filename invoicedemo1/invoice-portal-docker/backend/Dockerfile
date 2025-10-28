FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# 依赖：Flask/Waitress 后端，lxml XML校验，openpyxl 读 xlsx，pyjwt/bcrypt 做鉴权
RUN pip install --no-cache-dir flask waitress lxml openpyxl pyjwt bcrypt
COPY app.py /app/app.py
COPY schemas /app/schemas
# 通过 waitress 启动
CMD ["waitress-serve", "--port=5000", "--call", "app:create_app"]
