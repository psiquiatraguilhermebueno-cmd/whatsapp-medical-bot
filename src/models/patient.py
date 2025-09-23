# src/models/patient.py
from datetime import datetime
from uuid import uuid4
from src.models.user import db

class Patient(db.Model):
    __tablename__ = "patients"  # <- Admin espera 'patients' (plural)

    # vamos de UUID string pra não depender de autoincrement
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))

    name = db.Column(db.String(120), nullable=False)

    # campo que o Admin usa
    phone_e164 = db.Column(db.String(20), unique=True, nullable=False)

    # campos que o Admin exibe/filtra
    tags = db.Column(db.String(255))
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # compatibilidade futura (não atrapalha o Admin)
    email = db.Column(db.String(120))
    whatsapp_phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    cpf = db.Column(db.String(14))
    iclinic_id = db.Column(db.String(50), unique=True, nullable=True)
    telegram_chat_id = db.Column(db.String(50), unique=True)
    telegram_username = db.Column(db.String(100))

    def __repr__(self):
        return f"<Patient {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone_e164": self.phone_e164,
            "tags": self.tags,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
