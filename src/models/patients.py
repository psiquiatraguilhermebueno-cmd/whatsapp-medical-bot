# src/models/patients.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime
from src.models.user import db

class Patients(db.Model):
    __tablename__ = 'patients'
    __table_args__ = {'extend_existing': True}  # evita "already defined"

    id          = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name        = Column(String(100), nullable=False)
    phone_e164  = Column(String(20), nullable=False, unique=True)
    tags        = Column(Text)
    active      = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)

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
