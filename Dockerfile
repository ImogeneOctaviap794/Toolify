# 第一阶段：构建前端
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 第二阶段：Python 运行环境
FROM python:3.10-slim

WORKDIR /app

# 复制 Python 依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源代码
COPY *.py .
COPY config.example.yaml .

# 从第一阶段复制前端构建产物
COPY --from=frontend-builder /frontend/dist ./frontend/dist

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
	PYTHONIOENCODING=UTF-8 \
	PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "-u", "-m", "uvicorn"]

CMD ["main:app", "--host", "0.0.0.0", "--port", "8000"]