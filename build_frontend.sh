#!/bin/bash

# Build frontend script for Toolify Admin
echo "🔨 构建 Toolify Admin 前端管理界面..."

cd frontend || exit 1

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the frontend
echo "🏗️  Building production bundle..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 前端构建成功！"
    echo "📁 构建输出: frontend/dist/"
    echo ""
    echo "后续步骤:"
    echo "1. 重启 Toolify Admin 服务"
    echo "2. 访问管理界面: http://localhost:8000/admin"
else
    echo "❌ 构建失败！"
    exit 1
fi

