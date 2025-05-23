import os
from flask import Flask, render_template, request, jsonify, url_for, redirect
from app.models import db, AuditLog, login_manager
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import config
import jinja2
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf

# ユーティリティ関数
def nl2br(value):
    if not value:
        return ''
    return jinja2.utils.markupsafe.Markup(jinja2.utils.escape(value).replace('\n', '<br />'))

def create_app(config_name='default'):
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # 設定を適用
    app.config.from_object(config[config_name])
    
    # カスタムフィルターを追加
    app.jinja_env.filters['nl2br'] = nl2br
    
    # 日本語JSONレスポンス対応
    app.config['JSON_AS_ASCII'] = False
    
    # データベース初期化
    db.init_app(app)
    
    # CSRF保護の初期化
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # API エンドポイントは CSRF 保護から除外
    @csrf.exempt
    def csrf_exempt_api():
        if request.path.startswith('/api/') or request.path.startswith('/operator/api/'):
            return True
        return False
    
    # すべてのリクエストにCSRFトークンを追加
    @app.after_request
    def add_csrf_header(response):
        response.headers.set('X-CSRFToken', generate_csrf())
        return response
        
    # CSRF エラーハンドラー
    @app.errorhandler(400)
    def handle_csrf_error(e):
        if 'CSRF token is missing' in str(e) or 'CSRF token validation failed' in str(e):
            app.logger.error(f"CSRF エラー: {str(e)} - パス: {request.path}")
            return render_template('errors/csrf_error.html'), 400
        return e
    
    # ログイン管理の初期化
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'この機能を利用するにはログインが必要です。'
    login_manager.login_message_category = 'warning'
    
    # デバッグ用：リダイレクト先を表示
    @app.before_request
    def log_redirect():
        print(f"Request URL: {request.url}")
        print(f"Login view: {login_manager.login_view}")
        print(f"Login URL: {url_for(login_manager.login_view, _external=True)}")
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # ログ設定
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('アプリケーション起動')
    
    # アップロードディレクトリの確認
    for asset_type in app.config['ASSET_TYPES']:
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], asset_type)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
    
    # ルートの登録
    from app.routes.main import main_bp
    from app.routes.forklift import forklift_bp
    from app.routes.facility import facility_bp
    from app.routes.repair import repair_bp
    from app.routes.inspection import inspection_bp
    from app.routes.report_new import report_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.csv_upload import csv_upload_bp
    from app.routes.annual_inspection import annual_inspection_bp
    from app.routes.operator import operator_bp
    from app.routes.pdf_management import pdf_management_bp
    from app.routes.master import master_bp
    from app.routes.backup import backup_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(forklift_bp, url_prefix='/forklift')
    app.register_blueprint(facility_bp, url_prefix='/facility')
    app.register_blueprint(repair_bp, url_prefix='/repair')
    app.register_blueprint(inspection_bp, url_prefix='/inspection')
    app.register_blueprint(report_bp, url_prefix='/report')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(csv_upload_bp, url_prefix='/csv')
    app.register_blueprint(annual_inspection_bp, url_prefix='/annual-inspection')
    app.register_blueprint(operator_bp, url_prefix='/operator')
    app.register_blueprint(pdf_management_bp, url_prefix='/pdf-management')
    app.register_blueprint(master_bp, url_prefix='/master')
    app.register_blueprint(backup_bp, url_prefix='/backup')
    
    # 管理者ページのリダイレクト
    @app.route('/admin/users')
    def admin_users_redirect():
        return redirect(url_for('auth.user_list'))
    
    # エラーハンドラー
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # 監査ログ記録用のヘルパー関数
    @app.context_processor
    def utility_processor():
        def log_action(action, entity_type, entity_id=None, operator=None, details=None):
            if not operator:
                operator = request.form.get('operator', 'システム')
            
            log = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                operator=operator,
                details=details
            )
            db.session.add(log)
            db.session.commit()
            return ''
        
        return dict(log_action=log_action)
    
    # テンプレート用のグローバル変数
    @app.context_processor
    def inject_globals():
        from flask import session
        
        return {
            'current_year': datetime.now().year,
            'app_name': '倉庫修繕費管理システム',
            'asset_types': app.config['ASSET_TYPE_NAMES'],
            'forklift_types': app.config['FORKLIFT_TYPE_NAMES'],
            'power_sources': app.config['POWER_SOURCE_NAMES'],
            'repair_reasons': app.config['REPAIR_REASON_NAMES'],
            'asset_statuses': app.config['ASSET_STATUS_NAMES'],
            'repair_target_types': app.config['REPAIR_TARGET_TYPE_NAMES'],
            'repair_actions': app.config['REPAIR_ACTION_NAMES'],
            'ownership_types': app.config['OWNERSHIP_TYPE_NAMES'],
            'inspection_results': app.config['INSPECTION_RESULT_NAMES'],
            'inspection_types': app.config['INSPECTION_TYPES'],
            'current_user': current_user,
            'current_operator_name': session.get('current_operator_name', ''),
            'now': datetime.now
        }
    
    return app
