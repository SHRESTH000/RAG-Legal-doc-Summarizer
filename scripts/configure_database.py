"""
Helper script to configure database connection
"""

import os
import sys
from pathlib import Path

def setup_env_file():
    """Create .env file with database configuration"""
    env_path = Path(".env")
    
    print("="*60)
    print("Database Configuration Setup")
    print("="*60)
    print("\nPlease provide your PostgreSQL database credentials:\n")
    
    host = input("Database Host [localhost]: ").strip() or "localhost"
    port = input("Database Port [5432]: ").strip() or "5432"
    database = input("Database Name [legal_rag]: ").strip() or "legal_rag"
    user = input("Database User [postgres]: ").strip() or "postgres"
    password = input("Database Password: ").strip()
    
    if not password:
        print("\n⚠️  Warning: No password provided. You may need to set it manually.")
    
    env_content = f"""# Database Configuration
DB_HOST={host}
DB_PORT={port}
DB_NAME={database}
DB_USER={user}
DB_PASSWORD={password}
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Configuration saved to {env_path}")
    print("\nNext steps:")
    print("1. Create the database (if not exists):")
    print(f"   createdb {database}")
    print("\n2. Install schema:")
    print(f"   psql -d {database} -f database/schema.sql")
    print("\n3. Run setup verification:")
    print("   python scripts/setup_database.py")
    
    # Also update config.yaml
    config_path = Path("config/config.yaml")
    if config_path.exists():
        print(f"\n💡 Note: You can also edit {config_path} directly if preferred.")

if __name__ == "__main__":
    setup_env_file()
