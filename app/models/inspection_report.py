from . import db
from datetime import datetime

class InspectionReport(db.Model):
    __tablename__ = 'inspection_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    forklift_id = db.Column(db.Integer, db.ForeignKey('forklifts.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operators.id'), nullable=False)
    inspection_date = db.Column(db.Date, nullable=False)
    inspection_type = db.Column(db.String(50), nullable=False)  # daily, monthly, annual
    status = db.Column(db.String(20), nullable=False)  # passed, failed, pending
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    next_inspection_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100))

    # Relationships
    forklift = db.relationship('Forklift', backref=db.backref('inspection_reports', lazy=True))
    operator = db.relationship('Operator', backref=db.backref('inspection_reports', lazy=True))

    def __repr__(self):
        return f'<InspectionReport {self.id}: {self.forklift_id} - {self.inspection_date}>'