from app.models import db
from app.models.asset import Asset
from datetime import datetime
from config import Config
from sqlalchemy.ext.hybrid import hybrid_property

class Forklift(Asset):
    __tablename__ = 'forklifts'
    
    management_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    manufacturer = db.Column(db.String(50), nullable=False)
    forklift_type = db.Column(db.String(20), nullable=False)  # reach, counter
    power_source = db.Column(db.String(20), nullable=False)  # battery, diesel, gasoline, lpg
    model = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(50), nullable=False)
    # vehicle_id_number = db.Column(db.String(50), nullable=True, unique=True)  # 車体番号
    load_capacity = db.Column(db.Integer, nullable=False)  # kg
    manufacture_date = db.Column(db.Date, nullable=False)
    lift_height = db.Column(db.Integer, nullable=False)  # mm
    warehouse_group = db.Column(db.String(50), nullable=False)
    warehouse_number = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.String(10), nullable=False)
    operator = db.Column(db.String(50))
    updated_by = db.Column(db.String(100))
    
    # リレーションシップ
    repairs = db.relationship('ForkliftRepair', back_populates='forklift', cascade='all, delete-orphan')
    
    @hybrid_property
    def elapsed_years(self):
        if not self.manufacture_date:
            return None
        current_date = Config.CURRENT_DATE.date()
        delta = current_date - self.manufacture_date
        return delta.days / 365.25
    
    @property
    def type_name(self):
        return Config.FORKLIFT_TYPE_NAMES.get(self.forklift_type, self.forklift_type)
    
    @property
    def power_source_name(self):
        return Config.POWER_SOURCE_NAMES.get(self.power_source, self.power_source)
    
    def __repr__(self):
        return f'<Forklift {self.management_number}>'
    
    def to_dict(self):
        base_dict = super().to_dict()
        forklift_dict = {
            'management_number': self.management_number,
            'manufacturer': self.manufacturer,
            'forklift_type': self.forklift_type,
            'type_name': self.type_name,
            'power_source': self.power_source,
            'power_source_name': self.power_source_name,
            'model': self.model,
            'serial_number': self.serial_number,
            'vehicle_id_number': self.vehicle_id_number,
            'load_capacity': self.load_capacity,
            'manufacture_date': self.manufacture_date.strftime('%Y-%m-%d') if self.manufacture_date else None,
            'lift_height': self.lift_height,
            'elapsed_years': round(self.elapsed_years, 2) if self.elapsed_years is not None else None,
            'warehouse_group': self.warehouse_group,
            'warehouse_number': self.warehouse_number,
            'floor': self.floor,
            'operator': self.operator
        }
        return {**base_dict, **forklift_dict}

class ForkliftRepair(db.Model):
    __tablename__ = 'forklift_repairs'
    
    id = db.Column(db.Integer, primary_key=True)
    repair_date = db.Column(db.Date, nullable=False, index=True)
    forklift_id = db.Column(db.Integer, db.ForeignKey('forklifts.id'), nullable=False)
    target_management_number = db.Column(db.String(50), nullable=False)
    contractor = db.Column(db.String(100), nullable=False)
    repair_target_type = db.Column(db.String(50), nullable=False)
    repair_item = db.Column(db.String(200), nullable=False)
    repair_cost = db.Column(db.Integer, nullable=False)
    repair_reason = db.Column(db.String(50), nullable=False)
    hour_meter = db.Column(db.Integer)  # 修繕時のアワーメーター値
    photo_path = db.Column(db.String(255))
    quotation_path = db.Column(db.String(255))
    approval_document_path = db.Column(db.String(255))
    completion_report_path = db.Column(db.String(255))
    notes = db.Column(db.Text)
    operator = db.Column(db.String(100), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100))
    
    # リレーションシップ
    forklift = db.relationship('Forklift', back_populates='repairs')
    
    @property
    def repair_target_type_name(self):
        return Config.REPAIR_TARGET_TYPE_NAMES.get(self.repair_target_type, self.repair_target_type)
    
    @property
    def repair_reason_name(self):
        return Config.REPAIR_REASON_NAMES.get(self.repair_reason, self.repair_reason)
    
    def __repr__(self):
        return f'<ForkliftRepair {self.id} for {self.target_management_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'repair_date': self.repair_date.strftime('%Y-%m-%d') if self.repair_date else None,
            'forklift_id': self.forklift_id,
            'target_management_number': self.target_management_number,
            'contractor': self.contractor,
            'repair_target_type': self.repair_target_type,
            'repair_target_type_name': self.repair_target_type_name,
            'repair_item': self.repair_item,
            'repair_cost': self.repair_cost,
            'repair_reason': self.repair_reason,
            'repair_reason_name': self.repair_reason_name,
            'hour_meter': self.hour_meter,
            'photo_path': self.photo_path,
            'quotation_path': self.quotation_path,
            'approval_document_path': self.approval_document_path,
            'completion_report_path': self.completion_report_path,
            'notes': self.notes,
            'operator': self.operator,
            'version': self.version
        }
    
    def increment_version(self):
        self.version += 1
        return self.version

class ForkliftPrediction(db.Model):
    __tablename__ = 'forklift_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    forklift_id = db.Column(db.Integer, db.ForeignKey('forklifts.id'), nullable=False)
    annual_inspection_date = db.Column(db.Date)
    next_annual_inspection_date = db.Column(db.Date)
    battery_replacement_date = db.Column(db.Date)
    next_battery_replacement_date = db.Column(db.Date)
    
    # 古いタイヤ交換フィールド（後方互換性のため残す）
    tire_replacement_date = db.Column(db.Date)
    tire_type = db.Column(db.String(50))  # summer, winter, drive, caster
    next_tire_replacement_date = db.Column(db.Date)
    
    # 新しいタイヤ交換フィールド（タイヤタイプごと）
    drive_tire_replacement_date = db.Column(db.Date)
    next_drive_tire_replacement_date = db.Column(db.Date)
    caster_tire_replacement_date = db.Column(db.Date)
    next_caster_tire_replacement_date = db.Column(db.Date)
    other_tire_replacement_date = db.Column(db.Date)
    next_other_tire_replacement_date = db.Column(db.Date)
    other_tire_type = db.Column(db.String(50))  # その他タイヤの種類を記録
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100))
    annual_inspection_status = db.Column(db.String(20))  # passed, failed, pending
    annual_inspection_notes = db.Column(db.Text)
    annual_inspection_report = db.Column(db.String(255))  # 年次点検レポートのPDFパス
    
    # リレーションシップ
    forklift = db.relationship('Forklift')
    
    def __repr__(self):
        return f'<ForkliftPrediction {self.id} for forklift {self.forklift_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'forklift_id': self.forklift_id,
            'annual_inspection_date': self.annual_inspection_date.strftime('%Y-%m-%d') if self.annual_inspection_date else None,
            'next_annual_inspection_date': self.next_annual_inspection_date.strftime('%Y-%m-%d') if self.next_annual_inspection_date else None,
            'battery_replacement_date': self.battery_replacement_date.strftime('%Y-%m-%d') if self.battery_replacement_date else None,
            'next_battery_replacement_date': self.next_battery_replacement_date.strftime('%Y-%m-%d') if self.next_battery_replacement_date else None,
            
            # 古いタイヤ交換フィールド
            'tire_replacement_date': self.tire_replacement_date.strftime('%Y-%m-%d') if self.tire_replacement_date else None,
            'tire_type': self.tire_type,
            'next_tire_replacement_date': self.next_tire_replacement_date.strftime('%Y-%m-%d') if self.next_tire_replacement_date else None,
            
            # 新しいタイヤ交換フィールド
            'drive_tire_replacement_date': self.drive_tire_replacement_date.strftime('%Y-%m-%d') if self.drive_tire_replacement_date else None,
            'next_drive_tire_replacement_date': self.next_drive_tire_replacement_date.strftime('%Y-%m-%d') if self.next_drive_tire_replacement_date else None,
            'caster_tire_replacement_date': self.caster_tire_replacement_date.strftime('%Y-%m-%d') if self.caster_tire_replacement_date else None,
            'next_caster_tire_replacement_date': self.next_caster_tire_replacement_date.strftime('%Y-%m-%d') if self.next_caster_tire_replacement_date else None,
            'other_tire_replacement_date': self.other_tire_replacement_date.strftime('%Y-%m-%d') if self.other_tire_replacement_date else None,
            'next_other_tire_replacement_date': self.next_other_tire_replacement_date.strftime('%Y-%m-%d') if self.next_other_tire_replacement_date else None,
            'other_tire_type': self.other_tire_type,
            
            'annual_inspection_status': self.annual_inspection_status,
            'annual_inspection_notes': self.annual_inspection_notes,
            'annual_inspection_report': self.annual_inspection_report
        }