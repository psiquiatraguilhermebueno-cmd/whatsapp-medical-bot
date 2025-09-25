# src/models/patient.py
from datetime import datetime
from src.models.user import db

class Patient(db.Model):
    __tablename__ = 'patients'
    __table_args__ = {"extend_existing": True}  # permite reuso seguro da tabela

    id = db.Column(db.String(64), primary_key=True)  # compatível com TEXT no SQLite
    name = db.Column(db.String(100), nullable=False)
    phone_e164 = db.Column(db.String(20), unique=True, nullable=False)
    tags = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Patient {self.name} {self.phone_e164}>'

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone_e164": self.phone_e164,
            "tags": self.tags,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
