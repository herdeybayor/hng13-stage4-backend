#!/bin/bash
# Script to create initial migrations for all services

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Creating Initial Migrations${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Function to create migration for a service
create_migration() {
    local service=$1
    local message=$2
    
    echo -e "${YELLOW}📝 Creating migration for ${service}...${NC}"
    
    if [ ! -d "${service}" ]; then
        echo -e "${RED}❌ Service directory ${service} not found!${NC}"
        return 1
    fi
    
    cd "${service}"
    
    # Check if migrations already exist
    if [ "$(ls -A alembic/versions 2>/dev/null)" ]; then
        echo -e "${YELLOW}⚠️  Migrations already exist for ${service}. Skipping...${NC}"
        cd ..
        return 0
    fi
    
    # Create migration
    docker-compose exec -T "${service%-service}-service" alembic revision --autogenerate -m "${message}" || {
        echo -e "${RED}❌ Failed to create migration for ${service}${NC}"
        cd ..
        return 1
    }
    
    echo -e "${GREEN}✅ Migration created for ${service}${NC}"
    cd ..
    echo ""
}

# Check if Docker services are running
echo -e "${BLUE}Checking Docker services...${NC}"
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Services not running. Starting them...${NC}"
    docker-compose up -d postgres redis rabbitmq
    sleep 10
    docker-compose up -d user-service template-service
    sleep 5
fi

echo -e "${GREEN}✅ Services are running${NC}"
echo ""

# Create migrations
create_migration "user-service" "Initial migration - create users table"
create_migration "template-service" "Initial migration - create templates table"

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}🎉 All migrations created!${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Review the generated migrations in each service's alembic/versions/ directory"
echo -e "  2. Run 'make db-migrate' or restart services to apply migrations"
echo ""

