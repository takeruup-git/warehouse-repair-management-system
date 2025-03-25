from app.models import db
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from config import Config

# 資産の基本モデル
class Asset(db.Model):
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    asset_management_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    department = db.Column(db.String(50), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)
    acquisition_date = db.Column(db.Date, nullable=False)
    useful_life = db.Column(db.Integer, nullable=False)  # 年数
    depreciation_rate = db.Column(db.Float, nullable=False)
    acquisition_cost = db.Column(db.Integer, nullable=False)
    residual_value = db.Column(db.Integer, nullable=False)
    asset_status = db.Column(db.String(20), nullable=False, default='active')
    version = db.Column(db.Integer, nullable=False, default=1)  # 楽観的ロック用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def status_name(self):
        return Config.ASSET_STATUS_NAMES.get(self.asset_status, self.asset_status)
    
    @property
    def asset_status_name(self):
        return Config.ASSET_STATUS_NAMES.get(self.asset_status, self.asset_status)
    
    @property
    def asset_type_name(self):
        return Config.ASSET_TYPE_NAMES.get(self.asset_type, self.asset_type)
    
    @property
    def elapsed_years(self):
        """経過年数を計算"""
        if hasattr(self, 'manufacture_date'):
            start_date = self.manufacture_date
        elif hasattr(self, 'construction_date'):
            start_date = self.construction_date
        else:
            start_date = self.acquisition_date
            
        days_difference = (Config.CURRENT_DATE.date() - start_date).days
        return days_difference / 365.25  # うるう年も考慮した年数
    
    def __repr__(self):
        return f'<Asset {self.asset_management_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_management_number': self.asset_management_number,
            'department': self.department,
            'asset_type': self.asset_type,
            'asset_type_name': self.asset_type_name,
            'acquisition_date': self.acquisition_date.strftime('%Y-%m-%d') if self.acquisition_date else None,
            'useful_life': self.useful_life,
            'depreciation_rate': self.depreciation_rate,
            'acquisition_cost': self.acquisition_cost,
            'residual_value': self.residual_value,
            'asset_status': self.asset_status,
            'status_name': self.status_name,
            'asset_status_name': self.asset_status_name,
            'version': self.version,
            'elapsed_years': self.elapsed_years
        }
    
    def increment_version(self):
        self.version += 1
        return self.version