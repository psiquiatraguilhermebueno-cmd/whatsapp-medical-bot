from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminder.id'), nullable=False)
    response_data = db.Column(db.JSON, nullable=True)  # Para armazenar respostas de escalas
    media_url = db.Column(db.String(500), nullable=True)  # Para vídeos/fotos
    text_response = db.Column(db.Text, nullable=True)  # Para respostas de texto
    score = db.Column(db.Integer, nullable=True)  # Pontuação da escala
    is_alarming = db.Column(db.Boolean, default=False)  # Se a pontuação é alarmante
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Response {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'reminder_id': self.reminder_id,
            'response_data': self.response_data,
            'media_url': self.media_url,
            'text_response': self.text_response,
            'score': self.score,
            'is_alarming': self.is_alarming,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

