#!/bin/bash
# run-local.sh - Run RTSP Defect Detector locally

set -e

echo "========================================"
echo "RTSP Defect Detector - Local Runner"
echo "========================================"
echo ""

# Check if running in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "Please run this script from the project root"
    exit 1
fi

# Check Docker
echo "🔍 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker found"

# Check if config exists
if [ ! -f "backend/config.yaml" ]; then
    echo "⚠️  Config file not found, creating from example..."
    cp backend/config.example.yaml backend/config.yaml 2>/dev/null || true
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/data/captures
mkdir -p backend/logs
mkdir -p backend/models

# Pull latest images
echo "📥 Pulling images..."
docker-compose pull

# Build and start
echo "🏗️  Building and starting services..."
docker-compose up --build -d

echo ""
echo "========================================"
echo "✅ Services started successfully!"
echo "========================================"
echo ""
echo "📱 Web UI:     http://localhost:3000"
echo "🔌 API:        http://localhost:8000"
echo "📚 API Docs:   http://localhost:8000/docs"
echo ""
echo "📝 Configuration:"
echo "   Edit backend/config.yaml to add your RTSP cameras"
echo "   Then restart with: docker-compose restart"
echo ""
echo "🛑 To stop:    docker-compose down"
echo "📊 Logs:       docker-compose logs -f"
echo ""
