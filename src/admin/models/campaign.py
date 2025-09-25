# src/admin/models/campaign.py
import uuid
import json
from datetime import datetime
from sqlalchemy import Column, Text, Integer, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from src.models.user import db

def _json_dump(value):
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return None

def _json_load(value):
    try:
        return json.loads(value) if value else None
    except Exception:
        return None

class WACampaign(db.Model):
    __tablename__ = 'wa_campaigns'

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False)
    template_name = Column(Text, nullable=False)
    lang_code = Column(Text, nullable=False, default='pt_BR')
    params_mode = Column(Text, nullable=False)   # 'fixed' or 'per_recipient'
    fixed_params = Column(Text)                  # JSON serializado
    tz = Column(Text, nullable=False, default='America/Sao_Paulo')
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime)                    # NULL = sem fim
    frequency = Column(Text, nullable=False)     # 'once','daily','weekly','monthly','cron'
    days_of_week = Column(Text)                  # "1,3,5"
    day_of_month = Column(Integer)               # 1..31
    send_time = Column(Text, nullable=False)     # "HH:MM"
    cron_expr = Column(Text)
    status = Column(Text, nullable=False, default='active')  # 'active','paused','done'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    recipients = relationship("WACampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")
    runs = relationship("WACampaignRun", back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("params_mode in ('fixed','per_recipient')", name='check_params_mode'),
        CheckConstraint("frequency in ('once','daily','weekly','monthly','cron')", name='check_frequency'),
        CheckConstraint("status in ('active','paused','done')", name='check_status'),
    )

    @property
    def fixed_params_obj(self):
        return _json_load(self.fixed_params)

    @fixed_params_obj.setter
    def fixed_params_obj(self, value):
        self.fixed_params = _json_dump(value)

    def __repr__(self):
        return f'<WACampaign {self.name} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'template_name': self.template_name,
            'lang_code': self.lang_code,
            'params_mode': self.params_mode,
            'fixed_params': self.fixed_params_obj,
            'tz': self.tz,
            'start_at': self.start_at.isoformat() if self.start_at else None,
            'end_at': self.end_at.isoformat() if self.end_at else None,
            'frequency': self.frequency,
            'days_of_week': self.days_of_week,
            'day_of_month': self.day_of_month,
            'send_time': self.send_time,
            'cron_expr': self.cron_expr,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WACampaignRecipient(db.Model):
    __tablename__ = 'wa_campaign_recipients'

    campaign_id = Column(Text, ForeignKey('wa_campaigns.id', ondelete='CASCADE'), primary_key=True)
    phone_e164  = Column(Text, nullable=False, primary_key=True)
    per_params  = Column(Text)  # JSON serializado

    campaign = relationship("WACampaign", back_populates="recipients")

    @property
    def per_params_obj(self):
        return _json_load(self.per_params)

    @per_params_obj.setter
    def per_params_obj(self, value):
        self.per_params = _json_dump(value)

    def __repr__(self):
        return f'<WACampaignRecipient {self.phone_e164}>'

    def to_dict(self):
        return {
            'campaign_id': self.campaign_id,
            'phone_e164': self.phone_e164,
            'per_params': self.per_params_obj
        }

class WACampaignRun(db.Model):
    __tablename__ = 'wa_campaign_runs'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Text, ForeignKey('wa_campaigns.id', ondelete='CASCADE'), nullable=False)
    run_at      = Column(DateTime, nullable=False)
    phone_e164  = Column(Text, nullable=False)
    payload     = Column(Text)   # JSON serializado
    wa_response = Column(Text)   # JSON serializado
    status      = Column(Text, nullable=False)   # 'ok','error','skipped'
    error_message = Column(Text)

    campaign = relationship("WACampaign", back_populates="runs")

    __table_args__ = (
        CheckConstraint("status in ('ok','error','skipped')", name='check_run_status'),
    )

    @property
    def payload_obj(self):
        return _json_load(self.payload)

    @payload_obj.setter
    def payload_obj(self, value):
        self.payload = _json_dump(value)

    @property
    def wa_response_obj(self):
        return _json_load(self.wa_response)

    @wa_response_obj.setter
    def wa_response_obj(self, value):
        self.wa_response = _json_dump(value)

    def __repr__(self):
        return f'<WACampaignRun {self.id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'run_at': self.run_at.isoformat() if self.run_at else None,
            'phone_e164': self.phone_e164,
            'payload': self.payload_obj,
            'wa_response': self.wa_response_obj,
            'status': self.status,
            'error_message': self.error_message
        }
