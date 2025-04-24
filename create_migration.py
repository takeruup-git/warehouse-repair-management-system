from flask import Flask
from flask_migrate import Migrate, migrate
from app import create_app
from app.models import db

app = create_app()
migrate = Migrate(app, db)

with app.app_context():
    migrate.init_app(app, db)
    migrate.migrate(message="Add form templates table")
    print("Migration created successfully.")