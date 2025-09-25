# src/models/response.py
from datetime import datetime
from src.models.user import db

class Response(db.Model):
    __tablename__ = 'response'  # mantém o nome singular para compatibilidade

    id = db.Column(db.Integer, primary_key=True)

    # FK corrigida: agora aponta para 'patients.id' (plural) e casa com o tipo String(64)
    patient_id = db.Column(db.String(64), db.ForeignKey('patients.id'), nullable=False, index=True)

    # Mantém referência para a tabela 'reminder' (singular), que é o __tablename__ padrão da classe Reminder
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminder.id'), nullable=False, index=True)

    # Dados da resposta (ex.: respostas de escalas)
    response_data = db.Column(db.JSON, nullable=True)

    # Anexos e texto livre
    media_url = db.Column(db.String(500), nullable=True)
    text_response = db.Column(db.Text, nullable=True)

    # Pontuação de escala e flag clínica
    score = db.Column(db.Integer, nullable=True)
    is_alarming = db.Column(db.Boolean, default=False)

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
