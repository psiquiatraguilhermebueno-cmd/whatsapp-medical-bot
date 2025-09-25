from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from src.models.user import db

class Patient(db.Model):
    __tablename__ = "patients"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    # Telefone E.164 sem o '+', ex.: '5511912345678'
    phone_e164 = Column(String(20), unique=True, nullable=False, index=True)
    tags = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Patient {self.name} {self.phone_e164}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone_e164": self.phone_e164,
            "tags": self.tags,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
