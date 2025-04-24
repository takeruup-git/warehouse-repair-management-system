from app.models import db
from datetime import datetime

class FormTemplate(db.Model):
    __tablename__ = 'form_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    form_type = db.Column(db.String(50), nullable=False)  # 'periodic', 'battery', 'preshift'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    # セルマッピング情報（JSON形式で保存）
    cell_mapping = db.Column(db.Text)
    
    def __repr__(self):
        return f'<FormTemplate {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'form_type': self.form_type,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by,
            'cell_mapping': self.cell_mapping
        }