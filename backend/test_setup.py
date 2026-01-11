"""
Test script to verify backend setup and imports
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all critical imports work"""
    print("Testing imports...")
    
    try:
        # Core imports
        from app.core.config import settings
        print("✓ Config imported")
        
        from app.core.database import Base, engine, get_db
        print("✓ Database imported")
        
        # Models
        from app.models.models import Dataset, Cycle, Deviation
        print("✓ Models imported")
        
        # Schemas
        from app.schemas.dataset import DatasetCreate, DatasetResponse
        from app.schemas.cycle import CycleResponse, CycleDetailResponse
        from app.schemas.analysis import ComparisonResponse, DeviationAnalysisResponse
        print("✓ Schemas imported")
        
        # Services
        from app.services.dataset_service import DatasetService
        from app.services.cycle_service import CycleService
        from app.services.analysis_service import AnalysisService
        print("✓ Services imported")
        
        # API
        from app.api.v1.router import api_router
        print("✓ API router imported")
        
        # Main app
        from main import app
        print("✓ Main app imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        from app.core.config import settings
        
        print(f"  Project: {settings.PROJECT_NAME}")
        print(f"  Version: {settings.VERSION}")
        print(f"  Database: {settings.DATABASE_URL}")
        print(f"  Debug: {settings.DEBUG}")
        print("✓ Configuration OK")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def check_dependencies():
    """Check required packages"""
    print("\nChecking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'pydantic_settings',
        'pandas',
        'numpy',
        'scipy',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed")
        return True


if __name__ == "__main__":
    print("=" * 50)
    print("VerTac Backend - System Check")
    print("=" * 50)
    print()
    
    all_ok = True
    
    if not check_dependencies():
        all_ok = False
        print("\n⚠️  Please install dependencies first")
    else:
        if not test_config():
            all_ok = False
        
        if not test_imports():
            all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ Backend system check PASSED")
        print("\nYou can now run:")
        print("  uvicorn main:app --reload")
    else:
        print("❌ Backend system check FAILED")
        print("\nPlease fix the errors above")
    print("=" * 50)
