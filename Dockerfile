# ============================================
# 第一阶段：构建前端
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# 复制前端依赖文件（利用 Docker 层缓存）
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# ============================================
# 第二阶段：Python 运行环境
# ============================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如果需要）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖（利用 Docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制后端核心模块
COPY toolify_core/ ./toolify_core/

# 复制后端入口文件和配置
COPY main.py config_loader.py admin_auth.py init_admin.py ./
COPY config.example.yaml ./

# 从第一阶段复制前端构建产物
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# 创建非 root 用户（安全最佳实践）
RUN useradd -m -u 1000 toolify && \
    chown -R toolify:toolify /app

USER toolify

# 暴露端口
EXPOSE 8000

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/toolify/.local/bin:$PATH"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]