#!/bin/bash
# Script to create initial migrations locally (without Docker)

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Creating Migrations Locally${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env with DATABASE_URL and other settings${NC}"
    exit 1
fi

# Export environment variables
set -a
source .env
set +a

# Function to setup and create migration
setup_service() {
    local service=$1
    local message=$2
    
    echo -e "${YELLOW}📝 Setting up ${service}...${NC}"
    
    if [ ! -d "${service}" ]; then
        echo -e "${RED}❌ ${service} directory not found!${NC}"
        return 1
    fi
    
    cd "${service}"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    # Check if migrations already exist
    if [ "$(ls -A alembic/versions 2>/dev/null)" ]; then
        echo -e "${YELLOW}⚠️  Migrations already exist. Creating new revision...${NC}"
        alembic revision --autogenerate -m "${message}"
    else
        echo -e "${YELLOW}Creating initial migration...${NC}"
        alembic revision --autogenerate -m "${message}"
    fi
    
    echo -e "${GREEN}✅ Migration created for ${service}${NC}"
    
    deactivate
    cd ..
    echo ""
}

# Main execution
echo -e "${YELLOW}This script will:${NC}"
echo -e "  1. Create virtual environments for each service"
echo -e "  2. Install dependencies"
echo -e "  3. Generate initial Alembic migrations"
echo ""
echo -e "${YELLOW}Note: Ensure PostgreSQL is running and DATABASE_URL in .env is correct${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted${NC}"
    exit 1
fi

# Create migrations
setup_service "user-service" "Initial migration - create users table"
setup_service "template-service" "Initial migration - create templates table"

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}🎉 Migrations created!${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Review migrations in alembic/versions/ directories"
echo -e "  2. Apply migrations:"
echo -e "     ${YELLOW}cd user-service && source venv/bin/activate && alembic upgrade head${NC}"
echo -e "     ${YELLOW}cd template-service && source venv/bin/activate && alembic upgrade head${NC}"
echo ""
echo -e "  Or if using Docker:"
echo -e "     ${YELLOW}make db-migrate${NC}"
echo ""

