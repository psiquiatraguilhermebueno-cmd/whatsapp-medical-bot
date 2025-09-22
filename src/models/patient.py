# src/models/patient.py
import re
from datetime import datetime
from sqlalchemy import func
from src.models.user import db

# Regex simples para E.164 do Brasil (+55 e 10–11 dígitos)
E164_BR_RE = re.compile(r'^\+55\d{10,11}$')

def normalize_e164_br(raw: str) -> str:
    """
    Normaliza um telefone brasileiro para E.164:
      - remove caracteres não numéricos;
      - se não começar com 55, prefixa 55;
      - retorna com '+'.
    Aceita 10 dígitos (fixo) ou 11 (móvel) após 55.
    """
    if not raw:
        return ''
    digits = re.sub(r'\D+', '', raw)
    if not digits:
        return ''
    if digits.startswith('55'):
        num = digits
    else:
        num = '55' + digits
    return '+' + num

class Patient(db.Model):
    __tablename__ = 'patients'

    # Mantém seu esquema original
    id = db.Column(db.Integer, primary_key=True)  # autoincrement por padrão no SQLite/Postgres
    name = db.Column(db.String(100), nullable=False)

    # Campos legados (mantidos)
    phone_number = db.Column(db.String(20))           # legado/livre
    email = db.Column(db.String(120))
    birth_date = db.Column(db.Date)
    cpf = db.Column(db.String(14))
    iclinic_id = db.Column(db.String(50), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # WhatsApp
    whatsapp_phone = db.Column(db.String(20))         # legado/livre

    # Telegram
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=True)  # deixa explicitamente nullable
    telegram_username = db.Column(db.String(100))

    # 🔎 NOVO: telefone normalizado para o que o Admin/fluxos esperam
    # Mantemos nullable=True para não quebrar esquemas antigos; unicidade e índice
    phone_e164 = db.Column(db.String(20), unique=True, index=True, nullable=True)

    # (Opcional) tags simples, como você usa no Admin
    tags = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos (mantidos)
    reminders = db.relationship('Reminder', backref='patient', lazy=True, cascade='all, delete-orphan')
    responses = db.relationship('Response', backref='patient', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Patient {self.name} {self.phone_e164 or self.whatsapp_phone or self.phone_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone_number': self.phone_number,
            'whatsapp_phone': self.whatsapp_phone,
            'phone_e164': self.phone_e164,
            'email': self.email,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'cpf': self.cpf,
            'iclinic_id': self.iclinic_id,
            'telegram_chat_id': self.telegram_chat_id,
            'telegram_username': self.telegram_username,
            'tags': self.tags,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    # ✅ Fábrica segura para o Admin usar
    @staticmethod
    def create(name: str, phone_raw: str, tags: str | None = None) -> "Patient":
        """
        Cria paciente normalizando telefone para E.164 (Brasil).
        Preenche phone_e164 e também whatsapp_phone para compatibilidade.
        """
        phone = normalize_e164_br(phone_raw)
        if not phone or not E164_BR_RE.match(phone):
            raise ValueError("Telefone inválido: use formato +55XXXXXXXXXXX (10–11 dígitos após 55)")

        p = Patient(
            name=(name or '').strip(),
            phone_e164=phone,
            whatsapp_phone=phone,   # mantém coerência com campo legado
            tags=(tags or None),
            is_active=True
        )
        db.session.add(p)
        db.session.commit()
        return p
