# src/models/mood.py
from datetime import datetime, date
from src.models.user import db

# -----------------------------------------------------------------------------
# Shim de compatibilidade para "mood" e "mood_chart"
# - TODA referência a paciente usa: db.ForeignKey('patients.id') + String(64)
# - Evita erros "could not find table 'patient'"
# -----------------------------------------------------------------------------

class Mood(db.Model):
    __tablename__ = 'mood'

    id = db.Column(db.Integer, primary_key=True)

    # FK padronizada com o Patient shim (tabela 'patients', id String(64))
    patient_id = db.Column(
        db.String(64),
        db.ForeignKey('patients.id'),
        nullable=False,
        index=True,
    )

    # Campos mínimos/seguros (ajuste depois se quiser mais detalhes)
    score = db.Column(db.Integer)            # 0..10, por exemplo
    note = db.Column(db.Text)                # observação opcional
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamento opcional (útil pra consultas)
    patient = db.relationship('Patient', backref=db.backref('moods', lazy=True))

    def __repr__(self):
        return f'<Mood {self.id} p={self.patient_id} score={self.score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'score': self.score,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class MoodChart(db.Model):
    __tablename__ = 'mood_chart'

    id = db.Column(db.Integer, primary_key=True)

    # MESMA padronização de FK
    patient_id = db.Column(
        db.String(64),
        db.ForeignKey('patients.id'),
        nullable=False,
        index=True,
    )

    # Um ponto por dia (ou conforme seu uso atual)
    day = db.Column(db.Date, nullable=False, default=date.today)
    value = db.Column(db.Integer)  # ex.: 0..10
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref('mood_chart_entries', lazy=True))

    def __repr__(self):
        return f'<MoodChart {self.id} p={self.patient_id} day={self.day} value={self.value}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'day': self.day.isoformat() if self.day else None,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
