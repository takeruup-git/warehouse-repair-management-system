from . import db
from datetime import datetime

class Operator(db.Model):
    __tablename__ = 'operators'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    license_number = db.Column(db.String(50))
    license_expiry = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100))

    def __repr__(self):
        return f'<Operator {self.employee_id}: {self.name}>'