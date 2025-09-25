# src/models/medication.py
from datetime import datetime
from src.models.user import db

class Medication(db.Model):
    __tablename__ = 'medication'  # mantém o nome singular porque o Reminder referencia 'medication.id'

    id = db.Column(db.Integer, primary_key=True)

    # FK corrigida: aponta para 'patients.id' (plural) e casa com o tipo String(64)
    patient_id = db.Column(db.String(64), db.ForeignKey('patients.id'), nullable=False, index=True)

    # Campos usuais (seguros, não quebram uso atual)
    name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(120))
    frequency = db.Column(db.String(50))  # ex.: 'daily', 'bid', 'tid'
    notes = db.Column(db.Text)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relação para facilitar consultas (opcional, mas útil)
    patient = db.relationship('Patient', backref=db.backref('medications', lazy=True))

    def __repr__(self):
        return f'<Medication {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'name': self.name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
