from app import create_app
from app.models import db
from sqlalchemy import text
import os
import sqlite3
import sys

def fix_migration():
    try:
        app = create_app()
        
        print("Starting migration fix...")
        print(f"Python version: {sys.version}")
        print(f"Operating system: {os.name}")
        
        # Check if the operators and inspection_reports tables exist
        with app.app_context():
            try:
                # Create the tables if they don't exist
                from app.models.operator import Operator
                from app.models.inspection_report import InspectionReport
                
                # Check if tables exist
                inspector = db.inspect(db.engine)
                existing_tables = inspector.get_table_names()
                
                print(f"Existing tables: {existing_tables}")
                
                # Create operators table if it doesn't exist
                if 'operators' not in existing_tables:
                    print("Creating operators table...")
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
                        print("operators table created successfully.")
                    except Exception as e:
                        print(f"Error creating operators table: {e}")
                        # Continue anyway
                
                # Create inspection_reports table if it doesn't exist
                if 'inspection_reports' not in existing_tables:
                    print("Creating inspection_reports table...")
                    try:
                        # Create the table manually using SQL
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
                        print("inspection_reports table created successfully.")
                    except Exception as e:
                        print(f"Error creating inspection_reports table: {e}")
                
                # Check if alembic_version table exists
                if 'alembic_version' in existing_tables:
                    try:
                        # Update alembic_version table to include the new migration
                        db.session.execute(text("UPDATE alembic_version SET version_num = '003'"))
                        db.session.commit()
                        print("Updated alembic_version to '003'")
                    except Exception as e:
                        print(f"Error updating alembic_version: {e}")
                else:
                    try:
                        # Create alembic_version table if it doesn't exist
                        db.session.execute(text("""
                        CREATE TABLE alembic_version (
                            version_num VARCHAR(32) NOT NULL, 
                            PRIMARY KEY (version_num)
                        )
                        """))
                        db.session.execute(text("INSERT INTO alembic_version VALUES ('003')"))
                        db.session.commit()
                        print("Created alembic_version table with version '003'")
                    except Exception as e:
                        print(f"Error creating alembic_version table: {e}")
                
                print("Migration fix completed successfully.")
            
            except Exception as e:
                print(f"Error during migration fix: {e}")
                raise
    
    except Exception as e:
        print(f"Critical error during migration fix: {e}")
        print("Please make sure all dependencies are installed and try again.")
        print("If the problem persists, try running 'python init_db.py' first.")

if __name__ == '__main__':
    fix_migration()