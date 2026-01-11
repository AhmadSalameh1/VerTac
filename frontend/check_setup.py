"""
Frontend environment configuration checker
"""

import os
import json


def check_frontend():
    """Check frontend setup"""
    print("=" * 50)
    print("VerTac Frontend - System Check")
    print("=" * 50)
    print()
    
    frontend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check package.json
    package_json = os.path.join(frontend_dir, 'package.json')
    if os.path.exists(package_json):
        print("✓ package.json found")
        with open(package_json) as f:
            data = json.load(f)
            print(f"  Name: {data.get('name')}")
            print(f"  Version: {data.get('version')}")
    else:
        print("❌ package.json not found")
        return False
    
    # Check tsconfig
    tsconfig = os.path.join(frontend_dir, 'tsconfig.json')
    if os.path.exists(tsconfig):
        print("✓ tsconfig.json found")
    else:
        print("❌ tsconfig.json not found")
    
    # Check src directory
    src_dir = os.path.join(frontend_dir, 'src')
    if os.path.exists(src_dir):
        print("✓ src directory found")
        
        # Check key files
        key_files = [
            'index.tsx',
            'App.tsx',
            'services/api.ts',
            'pages/Dashboard.tsx',
            'pages/DatasetList.tsx',
            'pages/CycleViewer.tsx',
            'pages/Analysis.tsx',
            'components/CycleChart.tsx',
        ]
        
        for file in key_files:
            filepath = os.path.join(src_dir, file)
            if os.path.exists(filepath):
                print(f"  ✓ {file}")
            else:
                print(f"  ❌ {file} - MISSING")
    else:
        print("❌ src directory not found")
    
    # Check node_modules
    node_modules = os.path.join(frontend_dir, 'node_modules')
    if os.path.exists(node_modules):
        print("✓ node_modules found")
        print("  Dependencies installed")
    else:
        print("⚠️  node_modules not found")
        print("  Run: npm install")
    
    # Check .env
    env_file = os.path.join(frontend_dir, '.env')
    if os.path.exists(env_file):
        print("✓ .env found")
        with open(env_file) as f:
            for line in f:
                if line.strip():
                    print(f"  {line.strip()}")
    else:
        print("⚠️  .env not found")
        print("  Creating .env file...")
        with open(env_file, 'w') as f:
            f.write("REACT_APP_API_URL=http://localhost:8000/api/v1\n")
        print("  ✓ .env created")
    
    print("\n" + "=" * 50)
    print("Frontend setup check complete")
    print("\nTo start development:")
    print("  npm install  (if not done)")
    print("  npm start")
    print("=" * 50)


if __name__ == "__main__":
    check_frontend()
