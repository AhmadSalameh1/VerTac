#!/bin/bash
# VerTac Quick Start Script
# This script starts both backend and frontend servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  VerTac Quick Start${NC}"
echo -e "${GREEN}================================${NC}"
echo

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    echo "Please run setup first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r backend/requirements.txt"
    exit 1
fi

# Check if database exists
if [ ! -f "$BACKEND_DIR/vertac.db" ]; then
    echo -e "${YELLOW}Database not found. Initializing...${NC}"
    cd "$BACKEND_DIR"
    "$VENV_PYTHON" init_db.py
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ Database initialized${NC}"
    echo
fi

# Check if frontend dependencies are installed
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not found. Installing...${NC}"
    cd "$FRONTEND_DIR"
    npm install
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    echo
fi

# Function to cleanup on exit
cleanup() {
    echo
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${GREEN}Starting backend server...${NC}"
cd "$BACKEND_DIR"
"$VENV_PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for backend to start
echo "Waiting for backend to be ready..."
sleep 5
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend running on http://localhost:8000${NC}"
    echo -e "  API docs: ${GREEN}http://localhost:8000/docs${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo

# Start frontend
echo -e "${GREEN}Starting frontend server...${NC}"
cd "$FRONTEND_DIR"
BROWSER=none npm start > /dev/null 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for frontend to start
echo "Waiting for frontend to be ready..."
sleep 10
echo -e "${GREEN}✓ Frontend running on http://localhost:3000${NC}"
echo

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  System is ready!${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo "Access points:"
echo -e "  Frontend:    ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:    ${GREEN}http://localhost:8000/docs${NC}"
echo
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
