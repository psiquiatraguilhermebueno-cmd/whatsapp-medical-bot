from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    birth_date = db.Column(db.Date)
    cpf = db.Column(db.String(14))
    iclinic_id = db.Column(db.String(50), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Campos para WhatsApp
    whatsapp_phone = db.Column(db.String(20))
    
    # Campos para Telegram
    telegram_chat_id = db.Column(db.String(50), unique=True)
    telegram_username = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    reminders = db.relationship('Reminder', backref='patient', lazy=True, cascade='all, delete-orphan')
    responses = db.relationship('Response', backref='patient', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Patient {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone_number': self.phone_number,
            'email': self.email,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'cpf': self.cpf,
            'iclinic_id': self.iclinic_id,
            'whatsapp_phone': self.whatsapp_phone,
            'telegram_chat_id': self.telegram_chat_id,
            'telegram_username': self.telegram_username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

