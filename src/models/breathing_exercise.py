from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class BreathingExercise(db.Model):
    """Modelo para exercícios de respiração"""
    __tablename__ = 'breathing_exercise'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=5)
    instructions = db.Column(db.Text)
    audio_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BreathingExercise {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'instructions': self.instructions,
            'audio_url': self.audio_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

