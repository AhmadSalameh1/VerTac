#!/bin/bash

# VerTac v0.2.0 Quick Start Script
# This script sets up and starts the complete v0.2.0 system

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       VerTac v0.2.0 - Live Monitoring System         ║${NC}"
echo -e "${BLUE}║                  Quick Start                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section headers
print_section() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
print_section "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_success "Docker installed"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi
print_success "Docker Compose installed"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_success "Python 3 installed"

echo ""

# Option to start with Docker Compose
read -p "Start with Docker Compose? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_section "Starting services with Docker Compose..."
    
    if cd "$PROJECT_ROOT" && docker-compose up -d; then
        print_success "Services started successfully"
        echo ""
        echo -e "${GREEN}Service URLs:${NC}"
        echo -e "  Backend API:     ${BLUE}http://localhost:8000${NC}"
        echo -e "  Frontend:        ${BLUE}http://localhost:3000${NC}"
        echo -e "  InfluxDB:        ${BLUE}http://localhost:8086${NC}"
        echo -e "  PostgreSQL:      ${BLUE}localhost:5432${NC}"
        echo -e "  Redis:           ${BLUE}localhost:6379${NC}"
    else
        print_error "Failed to start services"
        exit 1
    fi
else
    print_section "Starting services manually..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$PROJECT_ROOT/backend/.venv" ]; then
        print_section "Creating Python virtual environment..."
        cd "$PROJECT_ROOT/backend"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -q -r requirements.txt
        print_success "Virtual environment created"
    else
        source "$PROJECT_ROOT/backend/.venv/bin/activate"
        print_success "Virtual environment activated"
    fi
    
    # Start backend in background
    print_section "Starting backend (port 8000)..."
    cd "$PROJECT_ROOT/backend"
    nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    BACKEND_PID=$!
    sleep 2
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend started (PID: $BACKEND_PID)"
    else
        print_error "Failed to start backend"
        exit 1
    fi
    
    # Start frontend in background
    print_section "Starting frontend (port 3000)..."
    cd "$PROJECT_ROOT/frontend"
    if [ ! -d "node_modules" ]; then
        npm install -q
    fi
    nohup npm start > frontend.log 2>&1 &
    FRONTEND_PID=$!
    sleep 5
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend started (PID: $FRONTEND_PID)"
    else
        print_error "Failed to start frontend"
        kill $BACKEND_PID
        exit 1
    fi
fi

echo ""

# Initialize v0.2.0 database schema
print_section "Initializing v0.2.0 database schema..."

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Run database initialization
    if cd "$PROJECT_ROOT/backend" && python3 init_v0.2.0_db.py; then
        print_success "Database schema initialized"
    else
        print_error "Failed to initialize database schema"
        echo "You may need to run manually: cd backend && python3 init_v0.2.0_db.py"
    fi
fi

echo ""

# Setup edge connector
print_section "Setting up edge connector..."

if [ ! -d "$PROJECT_ROOT/edge-connector/.venv" ]; then
    cd "$PROJECT_ROOT/edge-connector"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
    print_success "Edge connector environment created"
fi

echo ""

# Display next steps
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                      Setup Complete!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Open Frontend:${NC}"
echo "   Browser: ${BLUE}http://localhost:3000${NC}"
echo ""
echo "2. ${YELLOW}View API Docs:${NC}"
echo "   Browser: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "3. ${YELLOW}Start Edge Connector:${NC}"
echo "   Terminal: ${BLUE}cd edge-connector && source .venv/bin/activate && python connector.py${NC}"
echo ""
echo "4. ${YELLOW}Register and Monitor:${NC}"
echo "   - Navigate to Live Monitoring in frontend"
echo "   - Edge connector will auto-register"
echo "   - Start a cycle and watch real-time data flow"
echo ""
echo -e "${GREEN}📚 Documentation:${NC}"
echo "   - Architecture:         ${BLUE}./ARCHITECTURE_v0.2.0.md${NC}"
echo "   - Implementation Guide: ${BLUE}./IMPLEMENTATION_GUIDE_v0.2.0.md${NC}"
echo "   - Release Notes:        ${BLUE}./RELEASE_NOTES_v0.2.0.md${NC}"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "   - Check backend logs:  tail -f backend/backend.log"
echo "   - Check frontend logs: tail -f frontend/frontend.log"
echo "   - View running services: docker-compose ps"
echo "   - Stop all services: docker-compose down"
echo ""
echo -e "${BLUE}Version: 0.2.0${NC}"
echo -e "${BLUE}Release Date: January 11, 2026${NC}"
echo ""
