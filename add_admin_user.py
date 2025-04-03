from app import create_app
from app.models import db
from app.models.user import User
import sys

def add_admin_user(username, email, password):
    """初期管理者ユーザーを追加する"""
    app = create_app()
    
    with app.app_context():
        # 既存のユーザーをチェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"ユーザー '{username}' は既に存在します。")
            return
        
        # 管理者ユーザーを作成
        admin = User(
            username=username,
            email=email,
            password=password,
            full_name="システム管理者",
            role="admin"
        )
        
        db.session.add(admin)
        db.session.commit()
        print(f"管理者ユーザー '{username}' が正常に作成されました。")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用方法: python add_admin_user.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    add_admin_user(username, email, password)