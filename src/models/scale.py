from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Scale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 'PHQ-9', 'GAD-7', etc.
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    questions = db.Column(db.JSON, nullable=False)  # Lista de perguntas
    scoring_rules = db.Column(db.JSON, nullable=False)  # Regras de pontuação
    alarm_threshold = db.Column(db.Integer, nullable=False)  # Pontuação que gera alerta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Scale {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'questions': self.questions,
            'scoring_rules': self.scoring_rules,
            'alarm_threshold': self.alarm_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

