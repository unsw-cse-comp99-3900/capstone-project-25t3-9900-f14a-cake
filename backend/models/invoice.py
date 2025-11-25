"""Invoice model."""
from datetime import datetime
from . import db


class Invoice(db.Model):
    """Invoice model."""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    ocr_data = db.Column(db.JSON)  # Store OCR extracted JSON data
    xml_content = db.Column(db.Text)  # Store generated XML content
    validation_result = db.Column(db.JSON)  # Store validation results
    status = db.Column(db.String(50), default='processed', server_default='processed', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation of invoice
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'ocr_data': self.ocr_data,
            'xml_content': self.xml_content,
            'validation_result': self.validation_result,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Invoice {self.original_filename}>'

