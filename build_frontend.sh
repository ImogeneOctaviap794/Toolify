#!/bin/bash

# Build frontend script for Toolify
echo "🔨 Building Toolify Admin Frontend..."

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
    echo "✅ Frontend built successfully!"
    echo "📁 Build output: frontend/dist/"
    echo ""
    echo "Next steps:"
    echo "1. Restart the Toolify service"
    echo "2. Access admin interface at http://localhost:8000/admin"
else
    echo "❌ Build failed!"
    exit 1
fi

