#!/bin/bash

# Quick Start Script for Distributed Notification System
# This script automates the initial setup and launch of the system

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_message "❌ Docker is not installed. Please install Docker first." "$RED"
        exit 1
    fi
    print_message "✓ Docker found" "$GREEN"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_message "❌ Docker Compose is not installed. Please install Docker Compose first." "$RED"
        exit 1
    fi
    print_message "✓ Docker Compose found" "$GREEN"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_message "⚠ Python 3 is not installed. Some features may not work." "$YELLOW"
    else
        print_message "✓ Python 3 found" "$GREEN"
    fi
}

# Setup environment file
setup_environment() {
    print_header "Setting Up Environment"
    
    if [ -f .env ]; then
        print_message "⚠ .env file already exists. Skipping..." "$YELLOW"
        return
    fi
    
    if [ ! -f .env.example ]; then
        print_message "❌ .env.example not found!" "$RED"
        exit 1
    fi
    
    cp .env.example .env
    print_message "✓ Created .env file from .env.example" "$GREEN"
    print_message "⚠ Please update .env with your configuration!" "$YELLOW"
    
    # Ask if user wants to edit now
    read -p "Do you want to edit .env now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
}

# Create necessary directories
create_directories() {
    print_header "Creating Directories"
    
    mkdir -p logs
    mkdir -p backups
    mkdir -p rabbitmq-config
    
    print_message "✓ Directories created" "$GREEN"
}

# Start infrastructure services
start_infrastructure() {
    print_header "Starting Infrastructure Services"
    
    print_message "Starting PostgreSQL, Redis, and RabbitMQ..." "$BLUE"
    docker-compose up -d postgres redis rabbitmq
    
    print_message "Waiting for services to be healthy (30 seconds)..." "$YELLOW"
    sleep 30
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_message "✓ Infrastructure services started" "$GREEN"
    else
        print_message "❌ Failed to start infrastructure services" "$RED"
        exit 1
    fi
}

# Build application services
build_services() {
    print_header "Building Application Services"
    
    print_message "Building Docker images..." "$BLUE"
    docker-compose build
    
    print_message "✓ Services built successfully" "$GREEN"
}

# Start all services
start_all_services() {
    print_header "Starting All Services"
    
    print_message "Starting all services..." "$BLUE"
    docker-compose up -d
    
    print_message "Waiting for services to be ready (20 seconds)..." "$YELLOW"
    sleep 20
    
    print_message "✓ All services started" "$GREEN"
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    print_message "Running migrations for User Service..." "$BLUE"
    docker-compose exec -T user-service alembic upgrade head 2>/dev/null || print_message "⚠ User Service migrations not available yet" "$YELLOW"
    
    print_message "Running migrations for Template Service..." "$BLUE"
    docker-compose exec -T template-service alembic upgrade head 2>/dev/null || print_message "⚠ Template Service migrations not available yet" "$YELLOW"
    
    print_message "✓ Migrations complete" "$GREEN"
}

# Health check
health_check() {
    print_header "Health Check"
    
    print_message "Checking service health..." "$BLUE"
    
    # API Gateway
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        print_message "✓ API Gateway: Healthy" "$GREEN"
    else
        print_message "❌ API Gateway: Not responding" "$RED"
    fi
    
    # User Service
    if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        print_message "✓ User Service: Healthy" "$GREEN"
    else
        print_message "❌ User Service: Not responding" "$RED"
    fi
    
    # Template Service
    if curl -sf http://localhost:8002/health > /dev/null 2>&1; then
        print_message "✓ Template Service: Healthy" "$GREEN"
    else
        print_message "❌ Template Service: Not responding" "$RED"
    fi
    
    # RabbitMQ
    if curl -sf http://localhost:15672 > /dev/null 2>&1; then
        print_message "✓ RabbitMQ Management: Accessible" "$GREEN"
    else
        print_message "❌ RabbitMQ Management: Not accessible" "$RED"
    fi
}

# Show service status
show_status() {
    print_header "Service Status"
    docker-compose ps
}

# Print access information
print_access_info() {
    print_header "Access Information"
    
    echo -e "${GREEN}🚀 System is ready!${NC}\n"
    
    echo -e "${BLUE}API Endpoints:${NC}"
    echo -e "  📌 API Gateway:        ${GREEN}http://localhost:8000${NC}"
    echo -e "  📌 API Documentation:  ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  📌 User Service:       ${GREEN}http://localhost:8001/docs${NC}"
    echo -e "  📌 Template Service:   ${GREEN}http://localhost:8002/docs${NC}"
    
    echo -e "\n${BLUE}Management UIs:${NC}"
    echo -e "  📌 RabbitMQ:           ${GREEN}http://localhost:15672${NC} (admin/admin123)"
    
    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo -e "  📌 View logs:          ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  📌 Stop services:      ${YELLOW}docker-compose stop${NC}"
    echo -e "  📌 Restart services:   ${YELLOW}docker-compose restart${NC}"
    echo -e "  📌 View all commands:  ${YELLOW}make help${NC}"
    
    echo -e "\n${YELLOW}⚠️  Don't forget to configure your .env file with real credentials!${NC}"
}

# Main script
main() {
    print_message "
    ╔═══════════════════════════════════════════════╗
    ║   Distributed Notification System Setup      ║
    ║   Quick Start Script                          ║
    ╚═══════════════════════════════════════════════╝
    " "$BLUE"
    
    check_prerequisites
    setup_environment
    create_directories
    
    # Ask if user wants to build images
    read -p "Do you want to build Docker images now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_services
    fi
    
    start_infrastructure
    start_all_services
    
    # Ask if user wants to run migrations
    read -p "Do you want to run database migrations? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_migrations
    fi
    
    show_status
    
    # Wait a bit for services to fully start
    sleep 5
    
    health_check
    print_access_info
    
    print_message "\n✅ Setup complete! Happy coding!" "$GREEN"
}

# Run main function
main

