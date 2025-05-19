from app.models import db
from datetime import datetime

class FileMetadata(db.Model):
    __tablename__ = 'file_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, image, etc.
    entity_type = db.Column(db.String(50))  # forklift, facility, etc.
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<FileMetadata {self.original_filename}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_path': self.file_path,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_by': self.created_by
        }