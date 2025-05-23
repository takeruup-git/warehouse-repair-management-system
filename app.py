import os
import sys
from app import create_app
from flask_migrate import Migrate
from app.models import db

app = create_app()
migrate = Migrate(app, db)

def init_database():
    """データベースを初期化する"""
    with app.app_context():
        from app.models import db
        db.create_all()
        print("データベースが初期化されました。")

if __name__ == '__main__':
    # コマンドライン引数をチェック
    if len(sys.argv) > 1 and sys.argv[1] == 'init_db.py':
        init_database()
        sys.exit(0)
    
    # 通常の起動処理
    # 開発環境と本番環境で設定を分ける
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 53319))
    
    # データベースが存在しない場合は作成
    if not os.path.exists(os.path.join('instance', 'warehouse.db')):
        init_database()
    
    # アプリケーション起動
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
