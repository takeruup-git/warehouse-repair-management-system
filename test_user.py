from app import create_app
from app.models import db
from app.models.user import User

app = create_app()

with app.app_context():
    # Check if the users table exists
    try:
        users = User.query.all()
        print(f"Found {len(users)} users in the database:")
        for user in users:
            print(f"  - {user.username} (role: {user.role})")
    except Exception as e:
        print(f"Error querying users: {e}")