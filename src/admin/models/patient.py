import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from src.models.user import db

class AdminPatient(db.Model):
    __tablename__ = 'patients'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    phone_e164 = Column(Text, unique=True, nullable=False)  # "551499..." sem '+'
    tags = Column(ARRAY(Text), default=list)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminPatient {self.name} - {self.phone_e164}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'phone_e164': self.phone_e164,
            'tags': self.tags or [],
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

