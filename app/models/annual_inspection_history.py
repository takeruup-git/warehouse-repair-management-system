from app.models import db
from datetime import datetime

class AnnualInspectionHistory(db.Model):
    __tablename__ = 'annual_inspection_history'
    
    id = db.Column(db.Integer, primary_key=True)
    forklift_id = db.Column(db.Integer, db.ForeignKey('forklifts.id'), nullable=False)
    inspection_date = db.Column(db.Date, nullable=False)
    next_inspection_date = db.Column(db.Date)
    inspection_status = db.Column(db.String(20))  # passed, failed, pending
    inspection_notes = db.Column(db.Text)
    report_path = db.Column(db.String(255))  # 年次点検レポートのPDFパス
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    # リレーションシップ
    forklift = db.relationship('Forklift')
    
    def __repr__(self):
        return f'<AnnualInspectionHistory {self.id} for forklift {self.forklift_id} on {self.inspection_date}>'
