#!/usr/bin/env python
"""
Cross-platform database migration script for the Warehouse Repair Management System.
This script handles migrations in both Windows and Unix-like environments.
"""

import os
import sys
import time
import platform
import logging
import sqlite3
import subprocess
from pathlib import Path
from sqlalchemy import text, inspect
from app import create_app
from app.models import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)

def is_windows():
    """Check if the current platform is Windows."""
    return platform.system().lower() == 'windows'

def get_db_path(app):
    """Get the database path from the app configuration."""
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        # Convert relative path to absolute path
        relative_path = db_uri[10:]
        # Handle instance folder path
        if not os.path.isabs(relative_path):
            if relative_path.startswith('instance/'):
                # Remove 'instance/' prefix and join with app.instance_path
                instance_relative = relative_path[9:]
                return os.path.join(app.instance_path, instance_relative)
            else:
                # Join with current directory
                return os.path.abspath(relative_path)
        return relative_path
    return None

def check_db_connection(db_path, max_retries=3, retry_delay=1):
    """Check if the database is accessible with retry logic."""
    if not db_path:
        logger.error("Database path is None")
        return False
    
    # Create parent directory if it doesn't exist
    parent_dir = os.path.dirname(db_path)
    if not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
            logger.info(f"Created parent directory: {parent_dir}")
        except Exception as e:
            logger.error(f"Failed to create parent directory: {e}")
            return False
    
    # If database file doesn't exist, we'll try to connect anyway
    # SQLite will create the file if it doesn't exist
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found at: {db_path}, will be created if possible")
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1")
            conn.close()
            logger.info(f"Successfully connected to database at: {db_path}")
            return True
        except sqlite3.Error as e:
            logger.warning(f"Database connection attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    logger.error(f"Failed to connect to database after {max_retries} attempts")
    return False

def run_flask_db_command(command, app_path='app.py'):
    """Run a Flask db command with appropriate environment variables."""
    logger.info(f"Running Flask command: {command}")
    
    env = os.environ.copy()
    env['FLASK_APP'] = app_path
    
    if is_windows():
        # Windows-specific command execution
        cmd = f"set FLASK_APP={app_path} && python -m flask {command}"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        # Unix-like command execution
        cmd = f"python -m flask {command}"
        process = subprocess.Popen(cmd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stdout, stderr = process.communicate()
    stdout = stdout.decode('utf-8', errors='replace')
    stderr = stderr.decode('utf-8', errors='replace')
    
    logger.info(f"Command output: {stdout}")
    if stderr:
        logger.warning(f"Command errors: {stderr}")
    
    return process.returncode, stdout, stderr

def ensure_migrations_directory():
    """Ensure the migrations directory exists with the correct structure."""
    migrations_dir = Path('migrations')
    versions_dir = migrations_dir / 'versions'
    
    if not migrations_dir.exists():
        logger.info("Creating migrations directory")
        migrations_dir.mkdir(exist_ok=True)
        
    if not versions_dir.exists():
        logger.info("Creating migrations/versions directory")
        versions_dir.mkdir(exist_ok=True)
        
    # Check for env.py and script.py.mako
    env_py = migrations_dir / 'env.py'
    script_mako = migrations_dir / 'script.py.mako'
    
    if not env_py.exists() or not script_mako.exists():
        logger.info("Initializing migrations directory")
        run_flask_db_command('db init')

def fix_alembic_version(app, target_version='003'):
    """Fix the alembic_version table to ensure it has the correct version."""
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'alembic_version' in existing_tables:
            try:
                # Check current version
                result = db.session.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                current_version = result[0] if result else None
                logger.info(f"Current alembic version: {current_version}")
                
                if current_version != target_version:
                    logger.info(f"Updating alembic_version to '{target_version}'")
                    db.session.execute(text(f"UPDATE alembic_version SET version_num = '{target_version}'"))
                    db.session.commit()
            except Exception as e:
                logger.error(f"Error updating alembic_version: {e}")
                db.session.rollback()
        else:
            try:
                logger.info(f"Creating alembic_version table with version '{target_version}'")
                db.session.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL, 
                    PRIMARY KEY (version_num)
                )
                """))
                db.session.execute(text(f"INSERT INTO alembic_version VALUES ('{target_version}')"))
                db.session.commit()
            except Exception as e:
                logger.error(f"Error creating alembic_version table: {e}")
                db.session.rollback()

def ensure_required_tables(app):
    """Ensure all required tables exist in the database."""
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables: {existing_tables}")
        
        # Check for operators table
        if 'operators' not in existing_tables:
            logger.info("Creating operators table")
            try:
                db.session.execute(text("""
                CREATE TABLE operators (
                    id INTEGER NOT NULL, 
                    employee_id VARCHAR(50) NOT NULL, 
                    name VARCHAR(100) NOT NULL, 
                    department VARCHAR(100), 
                    license_number VARCHAR(50), 
                    license_expiry DATE, 
                    status VARCHAR(20), 
                    created_at DATETIME, 
                    updated_at DATETIME, 
                    updated_by VARCHAR(100), 
                    PRIMARY KEY (id),
                    UNIQUE (employee_id)
                )
                """))
                db.session.commit()
                logger.info("operators table created successfully")
            except Exception as e:
                logger.error(f"Error creating operators table: {e}")
                db.session.rollback()
        
        # Check for inspection_reports table
        if 'inspection_reports' not in existing_tables:
            logger.info("Creating inspection_reports table")
            try:
                db.session.execute(text("""
                CREATE TABLE inspection_reports (
                    id INTEGER NOT NULL, 
                    forklift_id INTEGER NOT NULL, 
                    operator_id INTEGER NOT NULL, 
                    inspection_date DATE NOT NULL, 
                    inspection_type VARCHAR(50) NOT NULL, 
                    status VARCHAR(20) NOT NULL, 
                    findings TEXT, 
                    recommendations TEXT, 
                    next_inspection_date DATE, 
                    created_at DATETIME, 
                    updated_at DATETIME, 
                    updated_by VARCHAR(100), 
                    PRIMARY KEY (id), 
                    FOREIGN KEY(forklift_id) REFERENCES forklifts (id), 
                    FOREIGN KEY(operator_id) REFERENCES operators (id)
                )
                """))
                db.session.commit()
                logger.info("inspection_reports table created successfully")
            except Exception as e:
                logger.error(f"Error creating inspection_reports table: {e}")
                db.session.rollback()

def run_migration():
    """Main function to run the database migration."""
    try:
        logger.info("Starting database migration")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Operating system: {platform.system()} {platform.release()}")
        
        # Create Flask app
        app = create_app()
        
        # Get database path
        db_path = get_db_path(app)
        logger.info(f"Database path: {db_path}")
        
        # Check database connection
        if db_path and not check_db_connection(db_path):
            logger.error("Cannot connect to database. Please check if the database file exists and is accessible.")
            return False
        
        # Ensure migrations directory exists
        ensure_migrations_directory()
        
        # Try to run the migration
        logger.info("Running database migration")
        returncode, stdout, stderr = run_flask_db_command('db upgrade')
        
        # If migration failed with "No such command 'db'" error
        if returncode != 0 and "No such command 'db'" in stderr:
            logger.warning("Flask-Migrate not properly installed or initialized. Attempting direct database setup.")
            
            # Create database tables directly using SQLAlchemy
            with app.app_context():
                logger.info("Creating database tables directly using SQLAlchemy")
                try:
                    db.create_all()
                    logger.info("Database tables created successfully")
                except Exception as e:
                    logger.error(f"Error creating database tables: {e}")
                    return False
            
            # Ensure required tables exist (for tables not defined in models)
            ensure_required_tables(app)
            
            # Fix alembic version
            fix_alembic_version(app)
            
            logger.info("Direct database setup completed")
            return True
            
        # If migration failed with "Can't locate revision" error
        elif returncode != 0 and "Can't locate revision" in stderr:
            logger.warning("Migration failed due to missing revision. Attempting to fix.")
            
            # Ensure required tables exist
            ensure_required_tables(app)
            
            # Fix alembic version
            fix_alembic_version(app)
            
            # Try migration again
            logger.info("Retrying migration after fixes")
            returncode, stdout, stderr = run_flask_db_command('db upgrade')
            
            if returncode == 0:
                logger.info("Migration completed successfully after fixes")
                return True
            else:
                logger.warning("Migration still failed after fixes. Attempting direct database setup.")
                
                # Create database tables directly as a last resort
                with app.app_context():
                    logger.info("Creating database tables directly using SQLAlchemy")
                    try:
                        db.create_all()
                        logger.info("Database tables created successfully")
                    except Exception as e:
                        logger.error(f"Error creating database tables: {e}")
                        return False
                
                # Ensure required tables exist (for tables not defined in models)
                ensure_required_tables(app)
                
                logger.info("Direct database setup completed")
                return True
        
        elif returncode == 0:
            logger.info("Migration completed successfully")
            return True
        else:
            logger.error(f"Migration failed with return code {returncode}")
            logger.error(f"Error message: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error during migration: {e}", exc_info=True)
        return False

def create_windows_batch_file():
    """Create a Windows batch file to run the migration script."""
    batch_content = """@echo off
echo Running database migration for Windows...
python run_migration.py
if %ERRORLEVEL% NEQ 0 (
    echo Migration failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
echo Migration completed successfully
"""
    
    with open('run_migration_windows.bat', 'w') as f:
        f.write(batch_content)
    
    logger.info("Created Windows batch file: run_migration_windows.bat")

if __name__ == '__main__':
    success = run_migration()
    
    # Create Windows batch file if on Windows
    if is_windows() and not os.path.exists('run_migration_windows.bat'):
        create_windows_batch_file()
    
    sys.exit(0 if success else 1)