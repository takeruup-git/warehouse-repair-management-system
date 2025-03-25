from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

from .operator import Operator

# 監査ログモデル
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    operator = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by {self.operator}>'