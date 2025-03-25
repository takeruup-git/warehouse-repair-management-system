from app import create_app

app = create_app()

if __name__ == '__main__':
    # データベース作成
    with app.app_context():
        from app.models import db
        db.create_all()
    
    # アプリケーション起動
    app.run(host='0.0.0.0', port=50978, debug=True)
