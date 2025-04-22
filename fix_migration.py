from app import create_app
from app.models import db
from sqlalchemy import text
import os
import sqlite3

def fix_migration():
    app = create_app()
    
    # Check if the operators and inspection_reports tables exist
    with app.app_context():
        # Create the tables if they don't exist
        from app.models.operator import Operator
        from app.models.inspection_report import InspectionReport
        
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"Existing tables: {existing_tables}")
        
        # Create tables if they don't exist
        if 'inspection_reports' not in existing_tables:
            print("Creating inspection_reports table...")
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
        
        print("Migration fix completed successfully.")
        
        # Update alembic_version table to include the new migration
        db.session.execute(text("UPDATE alembic_version SET version_num = '003'"))
        db.session.commit()
        print("Updated alembic_version to '003'")

if __name__ == '__main__':
    fix_migration()