import pytz
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
from croniter import croniter
from src.admin.models.campaign import WACampaign, WACampaignRecipient, WACampaignRun
from src.admin.services.whatsapp_service import AdminWhatsAppService
from src.models.user import db
import logging

logger = logging.getLogger(__name__)

class CampaignService:
    """Serviço para gerenciar campanhas WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = AdminWhatsAppService()
    
    def get_next_executions(self, campaign: WACampaign, limit: int = 5) -> List[datetime]:
        """
        Calcular próximas execuções de uma campanha
        
        Args:
            campaign: Campanha
            limit: Número máximo de execuções a retornar
            
        Returns:
            Lista de datetimes das próximas execuções
        """
        try:
            # Timezone da campanha
            tz = pytz.timezone(campaign.tz)
            now = datetime.now(tz)
            
            # Se campanha já terminou
            if campaign.end_at and now > campaign.end_at.replace(tzinfo=tz):
                return []
            
            executions = []
            
            if campaign.frequency == 'once':
                # Execução única
                if campaign.start_at.replace(tzinfo=tz) > now:
                    executions.append(campaign.start_at.replace(tzinfo=tz))
                    
            elif campaign.frequency == 'daily':
                # Diário
                current_date = max(now.date(), campaign.start_at.date())
                
                for i in range(limit * 2):  # Buffer para encontrar execuções válidas
                    exec_datetime = tz.localize(datetime.combine(current_date, campaign.send_time))
                    
                    if exec_datetime > now:
                        if not campaign.end_at or exec_datetime <= campaign.end_at.replace(tzinfo=tz):
                            executions.append(exec_datetime)
                            
                    current_date += timedelta(days=1)
                    
                    if len(executions) >= limit:
                        break
                        
            elif campaign.frequency == 'weekly':
                # Semanal
                if not campaign.days_of_week:
                    return []
                
                current_date = max(now.date(), campaign.start_at.date())
                
                for i in range(limit * 14):  # Buffer para encontrar execuções válidas
                    weekday = current_date.isoweekday()  # 1=Monday, 7=Sunday
                    
                    if weekday in campaign.days_of_week:
                        exec_datetime = tz.localize(datetime.combine(current_date, campaign.send_time))
                        
                        if exec_datetime > now:
                            if not campaign.end_at or exec_datetime <= campaign.end_at.replace(tzinfo=tz):
                                executions.append(exec_datetime)
                                
                    current_date += timedelta(days=1)
                    
                    if len(executions) >= limit:
                        break
                        
            elif campaign.frequency == 'monthly':
                # Mensal
                if not campaign.day_of_month:
                    return []
                
                current_date = max(now.date(), campaign.start_at.date())
                current_month = current_date.replace(day=1)
                
                for i in range(limit * 2):  # Buffer
                    try:
                        exec_date = current_month.replace(day=campaign.day_of_month)
                        exec_datetime = tz.localize(datetime.combine(exec_date, campaign.send_time))
                        
                        if exec_datetime > now:
                            if not campaign.end_at or exec_datetime <= campaign.end_at.replace(tzinfo=tz):
                                executions.append(exec_datetime)
                                
                    except ValueError:
                        # Dia não existe no mês (ex: 31 de fevereiro)
                        pass
                    
                    # Próximo mês
                    if current_month.month == 12:
                        current_month = current_month.replace(year=current_month.year + 1, month=1)
                    else:
                        current_month = current_month.replace(month=current_month.month + 1)
                    
                    if len(executions) >= limit:
                        break
                        
            elif campaign.frequency == 'cron':
                # CRON expression
                if not campaign.cron_expr:
                    return []
                
                try:
                    cron = croniter(campaign.cron_expr, now)
                    
                    for i in range(limit):
                        next_exec = cron.get_next(datetime)
                        
                        if campaign.end_at and next_exec > campaign.end_at.replace(tzinfo=tz):
                            break
                            
                        executions.append(next_exec)
                        
                except Exception as e:
                    logger.error(f"Invalid cron expression {campaign.cron_expr}: {e}")
                    return []
            
            return executions[:limit]
            
        except Exception as e:
            logger.error(f"Error calculating next executions for campaign {campaign.id}: {e}")
            return []
    
    def should_execute_now(self, campaign: WACampaign) -> bool:
        """
        Verificar se campanha deve ser executada agora
        
        Args:
            campaign: Campanha
            
        Returns:
            True se deve executar agora
        """
        try:
            # Timezone da campanha
            tz = pytz.timezone(campaign.tz)
            now = datetime.now(tz)
            
            # Verificar se está no período ativo
            if now < campaign.start_at.replace(tzinfo=tz):
                return False
                
            if campaign.end_at and now > campaign.end_at.replace(tzinfo=tz):
                return False
            
            # Verificar por frequência
            if campaign.frequency == 'once':
                # Verificar se já executou hoje
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                existing_run = WACampaignRun.query.filter(
                    WACampaignRun.campaign_id == campaign.id,
                    WACampaignRun.run_at >= today_start.astimezone(pytz.UTC),
                    WACampaignRun.run_at <= today_end.astimezone(pytz.UTC)
                ).first()
                
                if existing_run:
                    return False
                
                # Verificar se é o horário certo
                return now.time() >= campaign.send_time
                
            elif campaign.frequency == 'daily':
                # Verificar se já executou hoje
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                existing_run = WACampaignRun.query.filter(
                    WACampaignRun.campaign_id == campaign.id,
                    WACampaignRun.run_at >= today_start.astimezone(pytz.UTC),
                    WACampaignRun.run_at <= today_end.astimezone(pytz.UTC)
                ).first()
                
                if existing_run:
                    return False
                
                # Verificar se é o horário certo (com tolerância de 1 minuto)
                target_time = campaign.send_time
                current_time = now.time()
                
                # Converter para minutos para comparação
                target_minutes = target_time.hour * 60 + target_time.minute
                current_minutes = current_time.hour * 60 + current_time.minute
                
                return abs(current_minutes - target_minutes) <= 1
                
            elif campaign.frequency == 'weekly':
                if not campaign.days_of_week:
                    return False
                
                # Verificar dia da semana
                weekday = now.isoweekday()  # 1=Monday, 7=Sunday
                if weekday not in campaign.days_of_week:
                    return False
                
                # Verificar se já executou hoje
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                existing_run = WACampaignRun.query.filter(
                    WACampaignRun.campaign_id == campaign.id,
                    WACampaignRun.run_at >= today_start.astimezone(pytz.UTC),
                    WACampaignRun.run_at <= today_end.astimezone(pytz.UTC)
                ).first()
                
                if existing_run:
                    return False
                
                # Verificar horário
                target_time = campaign.send_time
                current_time = now.time()
                target_minutes = target_time.hour * 60 + target_time.minute
                current_minutes = current_time.hour * 60 + current_time.minute
                
                return abs(current_minutes - target_minutes) <= 1
                
            elif campaign.frequency == 'monthly':
                if not campaign.day_of_month:
                    return False
                
                # Verificar dia do mês
                if now.day != campaign.day_of_month:
                    return False
                
                # Verificar se já executou hoje
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                existing_run = WACampaignRun.query.filter(
                    WACampaignRun.campaign_id == campaign.id,
                    WACampaignRun.run_at >= today_start.astimezone(pytz.UTC),
                    WACampaignRun.run_at <= today_end.astimezone(pytz.UTC)
                ).first()
                
                if existing_run:
                    return False
                
                # Verificar horário
                target_time = campaign.send_time
                current_time = now.time()
                target_minutes = target_time.hour * 60 + target_time.minute
                current_minutes = current_time.hour * 60 + current_time.minute
                
                return abs(current_minutes - target_minutes) <= 1
                
            elif campaign.frequency == 'cron':
                if not campaign.cron_expr:
                    return False
                
                try:
                    # Verificar se o cron bate com agora (tolerância de 1 minuto)
                    cron = croniter(campaign.cron_expr, now - timedelta(minutes=1))
                    next_exec = cron.get_next(datetime)
                    
                    return abs((next_exec - now).total_seconds()) <= 60
                    
                except Exception as e:
                    logger.error(f"Error evaluating cron {campaign.cron_expr}: {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if campaign {campaign.id} should execute: {e}")
            return False
    
    def execute_campaign(self, campaign: WACampaign) -> Dict[str, Any]:
        """
        Executar campanha (enviar para todos os destinatários)
        
        Args:
            campaign: Campanha a executar
            
        Returns:
            Dict com resultado da execução
        """
        try:
            logger.info(f"Executing campaign {campaign.name} (ID: {campaign.id})")
            
            # Buscar destinatários
            recipients = WACampaignRecipient.query.filter_by(campaign_id=campaign.id).all()
            
            if not recipients:
                logger.warning(f"Campaign {campaign.id} has no recipients")
                return {
                    'success': False,
                    'error': 'No recipients found',
                    'sent_count': 0,
                    'error_count': 0
                }
            
            sent_count = 0
            error_count = 0
            
            for recipient in recipients:
                try:
                    # Montar parâmetros
                    params = {}
                    
                    if campaign.params_mode == 'fixed' and campaign.fixed_params:
                        params = campaign.fixed_params.copy()
                    elif campaign.params_mode == 'per_recipient':
                        if campaign.fixed_params:
                            params.update(campaign.fixed_params)
                        if recipient.per_params:
                            params.update(recipient.per_params)
                    
                    # Enviar template
                    result = self.whatsapp_service.send_template(
                        phone_e164=recipient.phone_e164,
                        template_name=campaign.template_name,
                        lang_code=campaign.lang_code,
                        params=params
                    )
                    
                    # Registrar execução
                    run = WACampaignRun(
                        campaign_id=campaign.id,
                        run_at=datetime.utcnow(),
                        phone_e164=recipient.phone_e164,
                        payload=result.get('payload'),
                        wa_response=result.get('wa_response'),
                        status='ok' if result['success'] else 'error',
                        error_message=result.get('error') if not result['success'] else None
                    )
                    
                    db.session.add(run)
                    
                    if result['success']:
                        sent_count += 1
                        logger.info(f"Template sent to {self.whatsapp_service.get_phone_masked(recipient.phone_e164)}")
                    else:
                        error_count += 1
                        logger.error(f"Failed to send template to {self.whatsapp_service.get_phone_masked(recipient.phone_e164)}: {result.get('error')}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Exception sending to {recipient.phone_e164}: {e}")
                    
                    # Registrar erro
                    run = WACampaignRun(
                        campaign_id=campaign.id,
                        run_at=datetime.utcnow(),
                        phone_e164=recipient.phone_e164,
                        payload=None,
                        wa_response=None,
                        status='error',
                        error_message=str(e)
                    )
                    
                    db.session.add(run)
            
            # Commit das execuções
            db.session.commit()
            
            logger.info(f"Campaign {campaign.id} executed: {sent_count} sent, {error_count} errors")
            
            return {
                'success': True,
                'sent_count': sent_count,
                'error_count': error_count,
                'total_recipients': len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Error executing campaign {campaign.id}: {e}")
            db.session.rollback()
            
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'error_count': 0
            }

