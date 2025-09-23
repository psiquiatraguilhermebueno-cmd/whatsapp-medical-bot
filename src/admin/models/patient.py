# src/models/patients.py
import uuid
from datetime import datetime
from src.models.user import db

class Patients(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    phone_e164 = db.Column(db.String(20), nullable=False, unique=True)
    tags = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Patients {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone_e164': self.phone_e164,
            'tags': self.tags,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
