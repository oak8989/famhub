#!/bin/bash
# =============================================================================
# Family Hub - Docker Build & Deploy Script
# =============================================================================

set -e

echo "🏠 Family Hub - Docker Deploy"
echo "=============================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    
    # Generate random JWT secret
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    
    # Update JWT_SECRET in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/change-this-to-a-random-secret-key/$JWT_SECRET/" .env
    else
        sed -i "s/change-this-to-a-random-secret-key/$JWT_SECRET/" .env
    fi
    
    echo "✅ Generated secure JWT_SECRET"
    echo ""
    echo "⚠️  Please review .env file and update settings if needed:"
    cat .env
    echo ""
    read -p "Press Enter to continue or Ctrl+C to edit .env first..."
fi

# Build the image
echo ""
echo "🔨 Building Docker image..."
docker compose build --no-cache

# Start the services
echo ""
echo "🚀 Starting services..."
docker compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo ""
echo "📊 Service Status:"
docker compose ps

# Health check
echo ""
echo "🏥 Health Check:"
if curl -s http://localhost:8001/api/health | grep -q "healthy"; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend may still be starting..."
fi

echo ""
echo "=============================="
echo "🎉 Family Hub is ready!"
echo ""
echo "📱 Access your app at: http://localhost:8001"
echo ""
echo "📋 Useful commands:"
echo "   View logs:    docker compose logs -f"
echo "   Stop:         docker compose down"
echo "   Restart:      docker compose restart"
echo "   Rebuild:      docker compose up -d --build"
echo ""
