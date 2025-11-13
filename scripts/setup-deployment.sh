#!/bin/bash
# Complete automated deployment setup script

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        Notification System - Deployment Setup           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Step 1: Environment Setup
echo -e "${BLUE}[1/6] 📋 Setting up environment...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file from .env.example${NC}"
        echo -e "${YELLOW}⚠️  Please update .env with your actual configuration!${NC}"
        echo -e "${YELLOW}   Especially: DATABASE_URL, SECRET_KEY, SMTP credentials${NC}"
        echo ""
        read -p "Press Enter when you've updated the .env file..."
    else
        echo -e "${RED}❌ .env.example not found. Please create .env manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi
echo ""

# Step 2: Make scripts executable
echo -e "${BLUE}[2/6] 🔧 Making scripts executable...${NC}"
chmod +x user-service/entrypoint.sh 2>/dev/null || true
chmod +x template-service/entrypoint.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
echo -e "${GREEN}✅ Scripts are executable${NC}"
echo ""

# Step 3: Clean up old containers
echo -e "${BLUE}[3/6] 🧹 Cleaning up old containers...${NC}"
docker-compose down -v 2>/dev/null || true
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Step 4: Build images
echo -e "${BLUE}[4/6] 🏗️  Building Docker images...${NC}"
docker-compose build --parallel
echo -e "${GREEN}✅ Images built successfully${NC}"
echo ""

# Step 5: Start infrastructure services
echo -e "${BLUE}[5/6] 🚀 Starting infrastructure services...${NC}"
docker-compose up -d postgres redis rabbitmq
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 15

# Wait for PostgreSQL
max_retries=30
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    echo -e "${YELLOW}⏳ Waiting for PostgreSQL... ($retry_count/$max_retries)${NC}"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    exit 1
fi
echo ""

# Step 6: Start application services
echo -e "${BLUE}[6/6] 🎯 Starting application services...${NC}"
docker-compose up -d
echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 10

# Check service health
echo ""
echo -e "${BLUE}Checking service health...${NC}"
services=("api-gateway:8000" "user-service:8001" "template-service:8002")
all_healthy=true

for service_port in "${services[@]}"; do
    service="${service_port%%:*}"
    port="${service_port##*:}"
    
    if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${service} is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  ${service} is starting...${NC}"
        all_healthy=false
    fi
done
echo ""

# Final status
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${GREEN}                  Deployment Complete! 🎉                  ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Service Status:${NC}"
docker-compose ps
echo ""
echo -e "${GREEN}🌐 Access Points:${NC}"
echo -e "  • API Gateway:       ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  • User Service:      ${YELLOW}http://localhost:8001/docs${NC}"
echo -e "  • Template Service:  ${YELLOW}http://localhost:8002/docs${NC}"
echo -e "  • RabbitMQ UI:       ${YELLOW}http://localhost:15672${NC} (admin/admin123)"
echo ""
echo -e "${GREEN}📝 Useful Commands:${NC}"
echo -e "  • View logs:         ${YELLOW}make logs${NC}"
echo -e "  • Check health:      ${YELLOW}make health${NC}"
echo -e "  • Stop services:     ${YELLOW}make stop${NC}"
echo -e "  • Restart services:  ${YELLOW}make restart${NC}"
echo -e "  • Run migrations:    ${YELLOW}make db-migrate${NC}"
echo ""

if [ "$all_healthy" = false ]; then
    echo -e "${YELLOW}⚠️  Some services are still starting. Wait a moment and run 'make health' to verify.${NC}"
fi

echo -e "${GREEN}✅ Your notification system is ready to use!${NC}"
echo ""

