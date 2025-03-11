import os
from flask import Flask, render_template, request, jsonify
from app.models import db, AuditLog
from app.models.forklift import Forklift, ForkliftRepair, ForkliftPrediction
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from app.models.master import Employee, Contractor, WarehouseGroup, Manufacturer, Budget, EquipmentLifespan
from app.models.inspection import BatteryFluidCheck, PeriodicSelfInspection, PreShiftInspection
from config import config
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def create_app(config_name='default'):
    app = Flask(__name__, 
                static_folder='app/static',
                template_folder='app/templates')
    
    # 設定を適用
    app.config.from_object(config[config_name])
    
    # 日本語JSONレスポンス対応
    app.config['JSON_AS_ASCII'] = False
    
    # データベース初期化
    db.init_app(app)
    
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
    from app.routes.report import report_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(forklift_bp, url_prefix='/forklift')
    app.register_blueprint(facility_bp, url_prefix='/facility')
    app.register_blueprint(repair_bp, url_prefix='/repair')
    app.register_blueprint(inspection_bp, url_prefix='/inspection')
    app.register_blueprint(report_bp, url_prefix='/report')
    app.register_blueprint(api_bp, url_prefix='/api')
    
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
            'inspection_types': app.config['INSPECTION_TYPES']
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # データベース作成
    with app.app_context():
        db.create_all()
    
    # アプリケーション起動
    app.run(host='0.0.0.0', port=50978, debug=True)