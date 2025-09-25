# src/models/medication.py
from datetime import datetime
from src.models.user import db

class Medication(db.Model):
    __tablename__ = "medication"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Paciente canônico: patients.id (STRING 64 para compatibilidade)
    patient_id = db.Column(db.String(64), db.ForeignKey("patients.id"), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(120))
    schedule = db.Column(db.String(120))  # ex.: "12:00, 20:00"
    notes = db.Column(db.Text)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Medication {self.name} for {self.patient_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "name": self.name,
            "dosage": self.dosage,
            "schedule": self.schedule,
            "notes": self.notes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# --- STUB para compatibilidade legada ---
# Alguns arquivos antigos podem tentar importar "MedicationConfirmation".
# Tornamos essa classe ABSTRATA para não criar tabela nem DDL.
class MedicationConfirmation(db.Model):
    __abstract__ = True
