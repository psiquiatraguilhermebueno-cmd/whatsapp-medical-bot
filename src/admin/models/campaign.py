# src/admin/models/campaign.py
from datetime import datetime
from uuid import uuid4
from src.models.user import db

# Observações importantes:
# - Nada de JSONB/ARRAY/UUID(dialect) -> usamos tipos portáveis: String, Integer, JSON, DateTime, etc.
# - Mantemos __tablename__ que o Admin espera: wa_campaigns, wa_campaign_recipients, wa_campaign_runs
# - Para compatibilidade com imports antigos, criamos aliases: WACampaign = WaCampaign, etc.

class WaCampaign(db.Model):
    __tablename__ = "wa_campaigns"

    # Em SQLite, usamos String(36) com UUID v4 como texto
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))

    name = db.Column(db.String(255), nullable=False)
    template_name = db.Column(db.String(255), nullable=False)
    lang_code = db.Column(db.String(10), nullable=False, default="pt_BR")

    # 'fixed' (usa fixed_params) ou 'per_recipient' (usa per_params por destinatário)
    params_mode = db.Column(db.String(20), nullable=False, default="fixed")

    # JSON portável (SQLAlchemy emula no SQLite)
    fixed_params = db.Column(db.JSON)  # ex.: {"1":"19/09/2025","2":"12:15"}

    tz = db.Column(db.String(64), nullable=False, default="America/Sao_Paulo")

    # Em SQLite não usamos timezone=True; guardamos UTC/naive conforme app
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime)  # NULL = sem fim

    # Frequência e agendamento
    frequency = db.Column(db.String(20), nullable=False, default="once")  # 'once','daily','weekly','monthly','cron'

    # Em vez de ARRAY(Integer), usamos string "1,4" (1=seg ... 7=dom) — simples e portátil
    days_of_week = db.Column(db.String(32))  # exemplo: "1,4"

    day_of_month = db.Column(db.Integer)     # 1..31
    # Em vez de Time(tz), guardamos "HH:MM" como string — simples e o Admin só exibe
    send_time = db.Column(db.String(8), nullable=False)  # "HH:MM"

    cron_expr = db.Column(db.String(64))     # quando frequency='cron'

    status = db.Column(db.String(20), nullable=False, default="active")  # 'active','paused','done'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<WaCampaign {self.name} - {self.status}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "template_name": self.template_name,
            "lang_code": self.lang_code,
            "params_mode": self.params_mode,
            "fixed_params": self.fixed_params,
            "tz": self.tz,
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "end_at": self.end_at.isoformat() if self.end_at else None,
            "frequency": self.frequency,
            "days_of_week": self.days_of_week,
            "day_of_month": self.day_of_month,
            "send_time": self.send_time,
            "cron_expr": self.cron_expr,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WaCampaignRecipient(db.Model):
    __tablename__ = "wa_campaign_recipients"

    campaign_id = db.Column(db.String(36), db.ForeignKey("wa_campaigns.id", ondelete="CASCADE"), primary_key=True)
    phone_e164 = db.Column(db.String(20), primary_key=True)

    # JSON por destinatário
    per_params = db.Column(db.JSON)

    # relacionamento opcional (só se algum lugar usar .campaign)
    # campaign = db.relationship("WaCampaign", backref=db.backref("recipients", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<WaCampaignRecipient {self.phone_e164}>"

    def to_dict(self):
        return {
            "campaign_id": str(self.campaign_id),
            "phone_e164": self.phone_e164,
            "per_params": self.per_params,
        }


class WaCampaignRun(db.Model):
    __tablename__ = "wa_campaign_runs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.String(36), db.ForeignKey("wa_campaigns.id", ondelete="CASCADE"), nullable=False)
    run_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    phone_e164 = db.Column(db.String(20), nullable=False)

    payload = db.Column(db.JSON)     # body enviado
    wa_response = db.Column(db.JSON) # resposta da API (JSON estruturado)

    status = db.Column(db.String(20), nullable=False, default="ok")  # 'ok','error','skipped'
    error_message = db.Column(db.Text)

    # relacionamento opcional
    # campaign = db.relationship("WaCampaign", backref=db.backref("runs", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<WaCampaignRun {self.id} - {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "campaign_id": str(self.campaign_id),
            "run_at": self.run_at.isoformat() if self.run_at else None,
            "phone_e164": self.phone_e164,
            "payload": self.payload,
            "wa_response": self.wa_response,
            "status": self.status,
            "error_message": self.error_message,
        }


# --- ALIASES DE COMPATIBILIDADE ---
# Se algum ponto do código ainda importar WACampaign / WACampaignRecipient / WACampaignRun,
# mantemos aliases para não quebrar.
WACampaign = WaCampaign
WACampaignRecipient = WaCampaignRecipient
WACampaignRun = WaCampaignRun
