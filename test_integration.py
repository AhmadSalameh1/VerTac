#!/usr/bin/env python3
"""Integration test script to verify the entire system works together"""

import sys
import time
import subprocess
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"

def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['RESET']}")

def check_database():
    """Check if database is initialized"""
    print_status("Checking database initialization...")
    db_path = BACKEND_DIR / "vertac.db"
    if not db_path.exists():
        print_status("Database not found, initializing...", "WARNING")
        result = subprocess.run(
            [str(VENV_PYTHON), "init_db.py"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_status("Database initialized successfully", "SUCCESS")
        else:
            print_status(f"Database initialization failed: {result.stderr}", "ERROR")
            return False
    else:
        print_status("Database exists", "SUCCESS")
    return True

def test_backend_api():
    """Test backend API endpoints"""
    print_status("Testing backend API...")
    
    # Start backend server in background
    print_status("Starting backend server...")
    backend_process = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print_status("Waiting for server to start...")
    max_retries = 10
    for i in range(max_retries):
        time.sleep(1)
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                print_status(f"Server ready after {i+1} seconds", "SUCCESS")
                break
        except:
            if i == max_retries - 1:
                raise
            continue
    
    try:
        # Test health endpoint
        print_status("Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_status("Health check passed", "SUCCESS")
        else:
            print_status(f"Health check failed: {response.status_code}", "ERROR")
            return False, backend_process
        
        # Test API root
        print_status("Testing API root...")
        response = requests.get("http://localhost:8000/api/v1/", timeout=5)
        if response.status_code == 200:
            print_status("API root accessible", "SUCCESS")
        else:
            print_status(f"API root failed: {response.status_code}", "WARNING")
        
        # Test datasets endpoint
        print_status("Testing datasets endpoint...")
        response = requests.get("http://localhost:8000/api/v1/datasets/", timeout=5)
        if response.status_code == 200:
            print_status(f"Datasets endpoint working (found {len(response.json())} datasets)", "SUCCESS")
        else:
            print_status(f"Datasets endpoint failed: {response.status_code}", "ERROR")
            return False, backend_process
        
        print_status("All backend tests passed!", "SUCCESS")
        return True, backend_process
        
    except requests.exceptions.ConnectionError:
        print_status("Failed to connect to backend server", "ERROR")
        return False, backend_process
    except Exception as e:
        print_status(f"Backend test failed: {str(e)}", "ERROR")
        return False, backend_process

def check_frontend():
    """Check if frontend compiles"""
    print_status("Checking frontend compilation...")
    frontend_dir = BASE_DIR / "frontend"
    
    # Check node_modules
    if not (frontend_dir / "node_modules").exists():
        print_status("node_modules not found, installing dependencies...", "WARNING")
        result = subprocess.run(
            ["npm", "install"],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print_status("npm install failed", "ERROR")
            return False
    
    # Test build
    print_status("Testing TypeScript compilation...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_status("Frontend compiles successfully", "SUCCESS")
        return True
    else:
        print_status(f"Frontend compilation failed: {result.stderr}", "ERROR")
        return False

def print_summary():
    """Print summary and next steps"""
    print("\n" + "="*60)
    print_status("INTEGRATION TEST COMPLETE", "SUCCESS")
    print("="*60)
    print("\nTo run the full application:")
    print("\n1. Start Backend:")
    print(f"   cd {BACKEND_DIR}")
    print(f"   {VENV_PYTHON} -m uvicorn main:app --reload")
    print("\n2. Start Frontend (in another terminal):")
    print(f"   cd {BASE_DIR / 'frontend'}")
    print("   npm start")
    print("\n3. Access the application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("\n" + "="*60)

def main():
    """Run all integration tests"""
    print_status("Starting VerTac Integration Tests", "INFO")
    print("="*60)
    
    backend_process = None
    
    try:
        # Test 1: Database
        if not check_database():
            print_status("Database check failed", "ERROR")
            sys.exit(1)
        
        print()
        
        # Test 2: Backend API
        success, backend_process = test_backend_api()
        if not success:
            print_status("Backend API tests failed", "ERROR")
            sys.exit(1)
        
        print()
        
        # Test 3: Frontend
        if not check_frontend():
            print_status("Frontend check failed", "ERROR")
            sys.exit(1)
        
        print()
        print_summary()
        
    except KeyboardInterrupt:
        print_status("\nTests interrupted by user", "WARNING")
    finally:
        # Clean up
        if backend_process:
            print_status("Stopping backend server...", "INFO")
            backend_process.terminate()
            backend_process.wait()
    
    sys.exit(0)

if __name__ == "__main__":
    main()
