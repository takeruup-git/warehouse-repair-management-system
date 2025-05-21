from app import create_app
from flask_migrate import Migrate
from app.models import db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    # データベース作成
    with app.app_context():
        from app.models import db
        db.create_all()
    
    # アプリケーション起動
    app.run(host='0.0.0.0', port=53319, debug=True)
