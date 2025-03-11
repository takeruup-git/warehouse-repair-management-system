from app.models import db
from app.models.asset import Asset
from datetime import datetime
from config import Config

class Facility(Asset):
    __tablename__ = 'facilities'
    
    warehouse_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    construction_date = db.Column(db.Date, nullable=False)
    main_structure = db.Column(db.String(100), nullable=False)
    ownership_type = db.Column(db.String(20), nullable=False)  # owned, leased
    floor_count = db.Column(db.Integer, nullable=False)
    
    # リレーションシップ
    repairs = db.relationship('FacilityRepair', back_populates='facility', cascade='all, delete-orphan')
    
    @property
    def ownership_type_name(self):
        return Config.OWNERSHIP_TYPE_NAMES.get(self.ownership_type, self.ownership_type)
    
    def __repr__(self):
        return f'<Facility {self.warehouse_number}>'
    
    def to_dict(self):
        base_dict = super().to_dict()
        facility_dict = {
            'warehouse_number': self.warehouse_number,
            'construction_date': self.construction_date.strftime('%Y-%m-%d') if self.construction_date else None,
            'main_structure': self.main_structure,
            'ownership_type': self.ownership_type,
            'ownership_type_name': self.ownership_type_name,
            'floor_count': self.floor_count
        }
        return {**base_dict, **facility_dict}

class FacilityRepair(db.Model):
    __tablename__ = 'facility_repairs'
    
    id = db.Column(db.Integer, primary_key=True)
    repair_date = db.Column(db.Date, nullable=False, index=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    target_warehouse_number = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.String(10), nullable=False)
    contractor = db.Column(db.String(100), nullable=False)
    repair_item = db.Column(db.String(200), nullable=False)
    repair_cost = db.Column(db.Integer, nullable=False)
    repair_reason = db.Column(db.String(50), nullable=False)
    photo_path = db.Column(db.String(255))
    quotation_path = db.Column(db.String(255))
    approval_document_path = db.Column(db.String(255))
    completion_report_path = db.Column(db.String(255))
    notes = db.Column(db.Text)
    operator = db.Column(db.String(100), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    facility = db.relationship('Facility', back_populates='repairs')
    
    @property
    def repair_reason_name(self):
        return Config.REPAIR_REASON_NAMES.get(self.repair_reason, self.repair_reason)
    
    def __repr__(self):
        return f'<FacilityRepair {self.id} for {self.target_warehouse_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'repair_date': self.repair_date.strftime('%Y-%m-%d') if self.repair_date else None,
            'facility_id': self.facility_id,
            'target_warehouse_number': self.target_warehouse_number,
            'floor': self.floor,
            'contractor': self.contractor,
            'repair_item': self.repair_item,
            'repair_cost': self.repair_cost,
            'repair_reason': self.repair_reason,
            'repair_reason_name': self.repair_reason_name,
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