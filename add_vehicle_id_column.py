from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # Add the vehicle_id_number column to the forklifts table
        conn.execute(text('ALTER TABLE forklifts ADD COLUMN vehicle_id_number VARCHAR(50)'))
        conn.commit()
        print("Added vehicle_id_number column to forklifts table")
        
        # Verify the column was added
        result = conn.execute(text('PRAGMA table_info(forklifts)'))
        for row in result:
            print(row)