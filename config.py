import os
from datetime import datetime

class Config:
    # アプリケーション設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    JSON_AS_ASCII = False  # 日本語JSONレスポンス対応
    
    # データベース設定
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # アップロードファイル設定
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大16MB
    
    # 日付設定
    CURRENT_DATE = datetime(2025, 3, 10)  # 現在日付の参照点
    
    # ページネーション設定
    ITEMS_PER_PAGE = 10
    
    # ログ設定
    LOG_FILE = os.path.join(os.getcwd(), 'app.log')
    
    # アプリケーション固有の設定
    ASSET_TYPES = ['forklift', 'facility', 'elevator', 'other', 'annual_inspection']
    ASSET_TYPE_NAMES = {
        'forklift': 'フォークリフト',
        'facility': '倉庫施設',
        'elevator': '昇降機',
        'other': 'その他',
        'annual_inspection': '年次点検'
    }
    
    # フォークリフト設定
    FORKLIFT_TYPES = ['reach', 'counter']
    FORKLIFT_TYPE_NAMES = {
        'reach': 'リーチ式',
        'counter': 'カウンター式'
    }
    
    POWER_SOURCES = ['battery', 'diesel', 'gasoline', 'lpg']
    POWER_SOURCE_NAMES = {
        'battery': 'バッテリー',
        'diesel': '軽油',
        'gasoline': 'ガソリン',
        'lpg': 'LPG'
    }
    
    # 修繕理由
    REPAIR_REASONS = ['failure', 'wear', 'accident', 'preventive', 'other']
    REPAIR_REASON_NAMES = {
        'failure': '故障',
        'wear': '劣化',
        'accident': '事故',
        'preventive': '予防',
        'other': 'その他'
    }
    
    # 資産ステータス
    ASSET_STATUSES = ['active', 'inactive', 'retired', 'under_repair']
    ASSET_STATUS_NAMES = {
        'active': '稼働中',
        'inactive': '非稼働',
        'retired': '廃車',
        'under_repair': '修繕中'
    }
    
    # 点検報告書設定
    INSPECTION_TYPES = {
        'battery_fluid': 'バッテリー液量点検表',
        'periodic_self': '定期自主検査記録表',
        'pre_shift': '始業前点検報告書'
    }
    
    # 修繕対象種別
    REPAIR_TARGET_TYPES = [
        'drive_tire', 'caster_tire', 'battery', 'fork', 'motor', 
        'hydraulic', 'brake', 'steering', 'electrical', 'structural', 'other'
    ]
    REPAIR_TARGET_TYPE_NAMES = {
        'drive_tire': 'ドライブタイヤ',
        'caster_tire': 'キャスタータイヤ',
        'battery': 'バッテリー',
        'fork': 'フォーク',
        'motor': 'モーター',
        'hydraulic': '油圧系統',
        'brake': 'ブレーキ',
        'steering': 'ステアリング',
        'electrical': '電気系統',
        'structural': '構造部分',
        'other': 'その他'
    }
    
    # 修繕アクション
    REPAIR_ACTIONS = ['X', '△', 'A', 'T', 'C', 'L', '-']
    REPAIR_ACTION_NAMES = {
        'X': '交換',
        '△': '修理',
        'A': '調整',
        'T': '締付',
        'C': '清掃',
        'L': '給油水',
        '-': '該当無'
    }
    
    # 所有形態
    OWNERSHIP_TYPES = ['owned', 'leased']
    OWNERSHIP_TYPE_NAMES = {
        'owned': '所有',
        'leased': '賃貸'
    }
    
    # 点検結果
    INSPECTION_RESULTS = ['good', 'bad']
    INSPECTION_RESULT_NAMES = {
        'good': '良',
        'bad': '不良'
    }

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev-app.db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'tests', 'uploads')
    
class TestConfig(TestingConfig):
    """Configuration for running integration tests"""
    pass

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}