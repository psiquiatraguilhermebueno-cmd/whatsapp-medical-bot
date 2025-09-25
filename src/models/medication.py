# src/models/medication.py
from datetime import datetime
from src.models.user import db


class Medication(db.Model):
    """
    Mantém o nome da tabela 'medication' (singular) porque outros pontos do
    sistema referenciam 'medication.id' (ex.: Reminder.medication_id).
    """
    __tablename__ = 'medication'

    id = db.Column(db.Integer, primary_key=True)

    # FK ALINHADA ao Patient shim (tabela 'patients', id = String(64))
    patient_id = db.Column(
        db.String(64),
        db.ForeignKey('patients.id'),
        nullable=False,
        index=True,
    )

    # Campos usuais
    name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(120))
    frequency = db.Column(db.String(50))  # ex.: 'daily', 'bid', 'tid'
    notes = db.Column(db.Text)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relação útil para consultas (opcional)
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


class MedicationConfirmation(db.Model):
    """
    Shim de compatibilidade: alguns pontos importam MedicationConfirmation
    de src.models.medication. Mantemos uma tabela simples para confirmações.
    """
    __tablename__ = 'medication_confirmations'

    id = db.Column(db.Integer, primary_key=True)

    # MESMO padrão de FK do Patient (tabela plural + String(64))
    patient_id = db.Column(
        db.String(64),
        db.ForeignKey('patients.id'),
        nullable=False,
        index=True,
    )

    # Opcional: vincular a um registro de medicação específico
    medication_id = db.Column(
        db.Integer,
        db.ForeignKey('medication.id'),
        nullable=True,
        index=True,
    )

    confirmed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='confirmed')  # 'confirmed', 'skipped', etc.

    # Relações (opcionais, mas convenientes)
    patient = db.relationship('Patient')
    medication = db.relationship('Medication')

    def __repr__(self):
        return f'<MedicationConfirmation {self.id} {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'medication_id': self.medication_id,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'status': self.status,
        }
