from app.models import db
from datetime import datetime

class OtherRepair(db.Model):
    __tablename__ = 'other_repairs'
    
    id = db.Column(db.Integer, primary_key=True)
    repair_date = db.Column(db.Date, nullable=False, index=True)
    target_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    repair_cost = db.Column(db.Integer, nullable=False)
    contractor = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    photo_path = db.Column(db.String(255))
    quotation_path = db.Column(db.String(255))
    operator = db.Column(db.String(100), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<OtherRepair {self.id} for {self.target_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'repair_date': self.repair_date.strftime('%Y-%m-%d') if self.repair_date else None,
            'target_name': self.target_name,
            'category': self.category,
            'repair_cost': self.repair_cost,
            'contractor': self.contractor,
            'notes': self.notes,
            'photo_path': self.photo_path,
            'quotation_path': self.quotation_path,
            'operator': self.operator,
            'version': self.version
        }
    
    def increment_version(self):
        self.version += 1
        return self.version