from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # Nome do medicamento
    dosage = db.Column(db.String(100), nullable=False)  # Dosagem (ex: "10mg", "2 comprimidos")
    frequency = db.Column(db.String(50), nullable=False)  # Frequência (ex: "daily", "twice_daily", "weekly")
    times = db.Column(db.JSON, nullable=False)  # Horários de administração ["08:00", "20:00"]
    instructions = db.Column(db.Text, nullable=True)  # Instruções especiais
    start_date = db.Column(db.Date, nullable=False)  # Data de início
    end_date = db.Column(db.Date, nullable=True)  # Data de fim (opcional)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Medication {self.name} - {self.dosage}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'name': self.name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'times': self.times,
            'instructions': self.instructions,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MedicationConfirmation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)  # Horário agendado
    confirmed_time = db.Column(db.DateTime, nullable=True)  # Horário confirmado pelo paciente
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, missed, late
    notes = db.Column(db.Text, nullable=True)  # Observações do paciente
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MedicationConfirmation {self.id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'medication_id': self.medication_id,
            'patient_id': self.patient_id,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'confirmed_time': self.confirmed_time.isoformat() if self.confirmed_time else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

