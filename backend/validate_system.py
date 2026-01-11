"""
Comprehensive system validation script
Tests all major components and integrations
"""

import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))


def validate_file_structure():
    """Validate project file structure"""
    print("\n📁 Validating File Structure...")
    
    required_files = {
        'backend': [
            'main.py',
            'requirements.txt',
            '.env',
            'app/__init__.py',
            'app/core/config.py',
            'app/core/database.py',
            'app/models/models.py',
            'app/api/v1/router.py',
            'app/api/v1/endpoints/datasets.py',
            'app/api/v1/endpoints/cycles.py',
            'app/api/v1/endpoints/analysis.py',
            'app/services/dataset_service.py',
            'app/services/cycle_service.py',
            'app/services/analysis_service.py',
            'app/schemas/dataset.py',
            'app/schemas/cycle.py',
            'app/schemas/analysis.py',
        ],
        'frontend': [
            'package.json',
            'tsconfig.json',
            '.env',
            'src/index.tsx',
            'src/App.tsx',
            'src/services/api.ts',
            'src/pages/Dashboard.tsx',
            'src/pages/DatasetList.tsx',
            'src/pages/CycleViewer.tsx',
            'src/pages/Analysis.tsx',
            'src/components/CycleChart.tsx',
        ]
    }
    
    all_ok = True
    backend_dir = Path(__file__).parent
    
    for component, files in required_files.items():
        component_dir = backend_dir.parent / component if component == 'frontend' else backend_dir
        print(f"\n  Checking {component}:")
        
        for file in files:
            file_path = component_dir / file
            if file_path.exists():
                print(f"    ✓ {file}")
            else:
                print(f"    ❌ {file} - MISSING")
                all_ok = False
    
    return all_ok


def validate_python_syntax():
    """Check Python files for syntax errors"""
    print("\n🐍 Validating Python Syntax...")
    
    import ast
    import glob
    
    python_files = glob.glob('**/*.py', recursive=True)
    errors = []
    
    for file in python_files:
        if 'venv' in file or '__pycache__' in file:
            continue
        
        try:
            with open(file, 'r') as f:
                ast.parse(f.read())
            print(f"  ✓ {file}")
        except SyntaxError as e:
            print(f"  ❌ {file}: {e}")
            errors.append((file, str(e)))
    
    if errors:
        print(f"\n❌ Found {len(errors)} syntax errors")
        return False
    else:
        print(f"\n✅ All Python files have valid syntax")
        return True


def validate_database_models():
    """Validate database models"""
    print("\n💾 Validating Database Models...")
    
    try:
        from app.models.models import Dataset, Cycle, Deviation
        from app.core.database import Base
        
        # Check that models are registered
        tables = Base.metadata.tables
        
        required_tables = ['datasets', 'cycles', 'deviations']
        for table_name in required_tables:
            if table_name in tables:
                table = tables[table_name]
                print(f"  ✓ {table_name} ({len(table.columns)} columns)")
            else:
                print(f"  ❌ {table_name} - NOT FOUND")
                return False
        
        print("\n✅ Database models are valid")
        return True
        
    except Exception as e:
        print(f"\n❌ Model validation error: {e}")
        return False


def validate_api_endpoints():
    """Validate API endpoint definitions"""
    print("\n🌐 Validating API Endpoints...")
    
    try:
        from app.api.v1.router import api_router
        
        # Count routes
        route_count = len(api_router.routes)
        print(f"  Found {route_count} routes")
        
        # Check endpoint modules
        from app.api.v1.endpoints import datasets, cycles, analysis
        
        modules = [
            ('datasets', datasets),
            ('cycles', cycles),
            ('analysis', analysis),
        ]
        
        for name, module in modules:
            if hasattr(module, 'router'):
                router = module.router
                print(f"  ✓ {name} router ({len(router.routes)} endpoints)")
            else:
                print(f"  ❌ {name} - NO ROUTER")
                return False
        
        print("\n✅ API endpoints are valid")
        return True
        
    except Exception as e:
        print(f"\n❌ API validation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_schemas():
    """Validate Pydantic schemas"""
    print("\n📋 Validating Schemas...")
    
    try:
        from app.schemas import dataset, cycle, analysis
        
        # Test schema imports
        schemas = [
            ('DatasetCreate', dataset.DatasetCreate),
            ('DatasetResponse', dataset.DatasetResponse),
            ('CycleResponse', cycle.CycleResponse),
            ('CycleDetailResponse', cycle.CycleDetailResponse),
            ('ComparisonResponse', analysis.ComparisonResponse),
            ('DeviationAnalysisResponse', analysis.DeviationAnalysisResponse),
        ]
        
        for name, schema_class in schemas:
            # Check it's a valid Pydantic model
            if hasattr(schema_class, 'model_fields'):
                fields = len(schema_class.model_fields)
                print(f"  ✓ {name} ({fields} fields)")
            else:
                print(f"  ❌ {name} - INVALID")
                return False
        
        print("\n✅ Schemas are valid")
        return True
        
    except Exception as e:
        print(f"\n❌ Schema validation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_services():
    """Validate service layer"""
    print("\n⚙️  Validating Services...")
    
    try:
        from app.services.dataset_service import DatasetService
        from app.services.cycle_service import CycleService
        from app.services.analysis_service import AnalysisService
        
        services = [
            ('DatasetService', DatasetService),
            ('CycleService', CycleService),
            ('AnalysisService', AnalysisService),
        ]
        
        for name, service_class in services:
            # Check required methods
            required_methods = ['__init__']
            has_methods = all(hasattr(service_class, method) for method in required_methods)
            
            if has_methods:
                methods = [m for m in dir(service_class) if not m.startswith('_')]
                print(f"  ✓ {name} ({len(methods)} public methods)")
            else:
                print(f"  ❌ {name} - MISSING METHODS")
                return False
        
        print("\n✅ Services are valid")
        return True
        
    except Exception as e:
        print(f"\n❌ Service validation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_full_validation():
    """Run all validation checks"""
    print("=" * 60)
    print("🔍 VerTac System Validation")
    print("=" * 60)
    
    checks = [
        ("File Structure", validate_file_structure),
        ("Python Syntax", validate_python_syntax),
        ("Database Models", validate_database_models),
        ("Schemas", validate_schemas),
        ("Services", validate_services),
        ("API Endpoints", validate_api_endpoints),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ {name} check failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("\nSystem is ready! You can start the backend with:")
        print("  uvicorn main:app --reload")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease fix the issues above before starting the backend")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
