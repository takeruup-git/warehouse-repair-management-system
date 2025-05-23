from app import create_app
from app.models import db
from app.models.user import User
import sys
import getpass

def add_admin_user(username=None, email=None, password=None):
    """初期管理者ユーザーを追加する"""
    app = create_app()
    
    # コマンドライン引数がない場合はインタラクティブに入力を求める
    if username is None:
        username = input("管理者ユーザー名を入力してください: ")
    if email is None:
        email = input("管理者メールアドレスを入力してください: ")
    if password is None:
        password = getpass.getpass("管理者パスワードを入力してください: ")
        password_confirm = getpass.getpass("パスワードを再入力してください: ")
        if password != password_confirm:
            print("パスワードが一致しません。")
            return
    
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
    # コマンドライン引数がある場合はそれを使用
    if len(sys.argv) == 4:
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
        add_admin_user(username, email, password)
    else:
        # 引数がない場合はインタラクティブモード
        add_admin_user()