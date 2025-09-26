#!/bin/bash

# Document Uploader Startup Script

echo "🚀 Starting Document Uploader..."
echo "================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if port 5001 is available
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  Port 5001 is already in use. The application might not start properly."
    echo "   You can change the port in docker-compose.yml if needed."
fi

# Start the application
echo "📦 Building and starting containers..."
docker-compose up -d --build

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 3

# Check if container is running
if docker-compose ps | grep -q "document-uploader"; then
    echo "✅ Document Uploader is running!"
    echo ""
    echo "🌐 Access the web interface at: http://localhost:5001"
    echo ""
    echo "📁 Upload directory: $(pwd)/uploads (inside container)"
    echo ""
    echo "🛑 To stop: docker-compose down"
    echo "📊 View logs: docker-compose logs -f"
else
    echo "❌ Failed to start Document Uploader"
    echo "📊 Check logs: docker-compose logs"
    exit 1
fi
