# src/admin/models/campaign.py
from datetime import datetime, time
from sqlalchemy import Column, String, Boolean, DateTime, Time, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import relationship
from src.models.user import db

# Em SQLite, use tipos simples e JSON nativo do SQLAlchemy (mapeado como TEXT)
JSONType = SQLITE_JSON

class WaCampaign(db.Model):
    __tablename__ = 'wa_campaigns'

    id = Column(String(64), primary_key=True)  # string UUID gerada na app, opcional
    name = Column(Text, nullable=False)
    template_name = Column(Text, nullable=False)
    lang_code = Column(Text, nullable=False, default='pt_BR')
    params_mode = Column(Text, nullable=False)  # 'fixed' or 'per_recipient'
    fixed_params = Column(JSONType)  # {"1":"19/09/2025","2":"12:15"}
    tz = Column(Text, nullable=False, default='America/Sao_Paulo')
    start_at = Column(DateTime, nullable=False)  # sem timezone para SQLite
    end_at = Column(DateTime)  # NULL = sem fim
    frequency = Column(Text, nullable=False)  # 'once','daily','weekly','monthly','cron'
    # Em SQLite evite ARRAY — se precisar, serialize no JSON
    days_of_week = Column(JSONType)  # ex.: [1, 4] (1=seg, 4=qui)
    day_of_month = Column(Integer)   # 1..31
    send_time = Column(Time, nullable=False)  # HH:MM
    cron_expr = Column(Text)
    status = Column(Text, nullable=False, default='active')  # 'active','paused','done'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    recipients = relationship("WaCampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")
    runs = relationship("WaCampaignRun", back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("params_mode IN ('fixed', 'per_recipient')", name='check_params_mode'),
        CheckConstraint("frequency IN ('once', 'daily', 'weekly', 'monthly', 'cron')", name='check_frequency'),
        CheckConstraint("status IN ('active', 'paused', 'done')", name='check_status'),
    )

    def __repr__(self):
        return f'<WaCampaign {self.name} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'template_name': self.template_name,
            'lang_code': self.lang_code,
            'params_mode': self.params_mode,
            'fixed_params': self.fixed_params,
            'tz': self.tz,
            'start_at': self.start_at.isoformat() if self.start_at else None,
            'end_at': self.end_at.isoformat() if self.end_at else None,
            'frequency': self.frequency,
            'days_of_week': self.days_of_week,
            'day_of_month': self.day_of_month,
            'send_time': self.send_time.strftime('%H:%M') if self.send_time else None,
            'cron_expr': self.cron_expr,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WaCampaignRecipient(db.Model):
    __tablename__ = 'wa_campaign_recipients'

    campaign_id = Column(String(64), ForeignKey('wa_campaigns.id', ondelete='CASCADE'), primary_key=True)
    phone_e164 = Column(Text, nullable=False, primary_key=True)
    per_params = Column(JSONType)  # se params_mode='per_recipient'

    campaign = relationship("WaCampaign", back_populates="recipients")

    def __repr__(self):
        return f'<WaCampaignRecipient {self.phone_e164}>'

    def to_dict(self):
        return {
            'campaign_id': self.campaign_id,
            'phone_e164': self.phone_e164,
            'per_params': self.per_params
        }

class WaCampaignRun(db.Model):
    __tablename__ = 'wa_campaign_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(64), ForeignKey('wa_campaigns.id', ondelete='CASCADE'), nullable=False)
    run_at = Column(DateTime, nullable=False)
    phone_e164 = Column(Text, nullable=False)
    payload = Column(JSONType)
    wa_response = Column(JSONType)
    status = Column(Text, nullable=False)  # 'ok','error','skipped'
    error_message = Column(Text)

    campaign = relationship("WaCampaign", back_populates="runs")

    __table_args__ = (
        CheckConstraint("status IN ('ok', 'error', 'skipped')", name='check_run_status'),
    )

    def __repr__(self):
        return f'<WaCampaignRun {self.id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'run_at': self.run_at.isoformat() if self.run_at else None,
            'phone_e164': self.phone_e164,
            'payload': self.payload,
            'wa_response': self.wa_response,
            'status': self.status,
            'error_message': self.error_message
        }
