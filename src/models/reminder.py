# src/models/reminder.py
from datetime import datetime, time
from src.models.user import db

class Reminder(db.Model):
    __tablename__ = "reminder"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)

    # FK corrigida: a tabela canônica de pacientes é 'patients'
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False,
    )

    # Tipos de lembrete: 'scale', 'task', 'motivational', 'medication', 'breathing', 'mood_chart'
    reminder_type = db.Column(db.String(50), nullable=False)

    # Para lembretes de escala
    scale_type = db.Column(db.String(50), nullable=True)  # 'PHQ-9', 'GAD-7', etc.

    # Para lembretes de medicação
    medication_id = db.Column(db.Integer, db.ForeignKey("medication.id"), nullable=True)

    # Para exercícios de respiração
    breathing_exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("breathing_exercise.id"),
        nullable=True,
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Frequência: 'daily', 'weekly', 'monthly', 'once', 'custom'
    frequency = db.Column(db.String(50), nullable=False)

    # Horário agendado
    scheduled_time = db.Column(db.Time, nullable=False)

    # Próxima data de envio
    next_send_date = db.Column(db.DateTime, nullable=False)

    # Para frequências customizadas (dias da semana, etc.)
    # Observação: db.JSON funciona em SQLite via emulação; mantido aqui.
    custom_schedule = db.Column(db.JSON, nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Reminder {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "reminder_type": self.reminder_type,
            "scale_type": self.scale_type,
            "medication_id": self.medication_id,
            "breathing_exercise_id": self.breathing_exercise_id,
            "title": self.title,
            "description": self.description,
            "frequency": self.frequency,
            "scheduled_time": self.scheduled_time.strftime("%H:%M")
            if self.scheduled_time
            else None,
            "next_send_date": self.next_send_date.isoformat()
            if self.next_send_date
            else None,
            "custom_schedule": self.custom_schedule,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
