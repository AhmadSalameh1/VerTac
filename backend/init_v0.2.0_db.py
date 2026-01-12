#!/usr/bin/env python3
"""
Initialize v0.2.0 database schema
Run this script to create live monitoring tables
"""

import os
import sys
import psycopg2
from pathlib import Path

def init_database():
    """Initialize database with v0.2.0 schema"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'vertac'),
        'user': os.getenv('POSTGRES_USER', 'vertac'),
        'password': os.getenv('POSTGRES_PASSWORD', 'vertac123')
    }
    
    print("🗄️  Initializing VerTac v0.2.0 Database Schema")
    print(f"📍 Connecting to: {db_params['host']}:{db_params['port']}/{db_params['database']}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Read migration SQL
        migration_file = Path(__file__).parent / 'migrations' / 'v0.2.0_live_tables.sql'
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            sys.exit(1)
        
        print(f"📖 Reading migration: {migration_file.name}")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        print("⚙️  Executing migration...")
        cursor.execute(migration_sql)
        
        print("✅ Migration executed successfully")
        
        # Verify tables created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'live_%'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   ✓ {table[0]}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n✅ Database initialization complete!")
        print("\n💡 Next steps:")
        print("   1. Start the backend: cd backend && python main.py")
        print("   2. Start the edge connector: cd edge-connector && python connector.py")
        print("   3. Open frontend: http://localhost:3000")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
