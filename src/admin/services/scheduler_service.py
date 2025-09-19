import logging
import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import pytz
from src.admin.models.campaign import WACampaign
from src.admin.services.campaign_service import CampaignService
from src.models.user import db

logger = logging.getLogger(__name__)

class CampaignSchedulerService:
    """Serviço de agendamento automático de campanhas"""
    
    def __init__(self):
        self.scheduler = None
        self.campaign_service = CampaignService()
        self.is_running = False
        self._lock = threading.Lock()
    
    def start(self):
        """Iniciar o scheduler"""
        with self._lock:
            if self.is_running:
                logger.warning("Scheduler already running")
                return
            
            try:
                # Configurar executor
                executors = {
                    'default': ThreadPoolExecutor(max_workers=3)
                }
                
                # Configurar scheduler
                self.scheduler = BackgroundScheduler(
                    executors=executors,
                    timezone=pytz.timezone('America/Sao_Paulo')
                )
                
                # Job principal: verificar campanhas a cada minuto
                self.scheduler.add_job(
                    func=self._check_campaigns,
                    trigger=IntervalTrigger(seconds=60),
                    id='campaign_checker',
                    name='Campaign Checker',
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True
                )
                
                # Job de limpeza: limpar logs antigos a cada 6 horas
                self.scheduler.add_job(
                    func=self._cleanup_old_logs,
                    trigger=IntervalTrigger(hours=6),
                    id='log_cleanup',
                    name='Log Cleanup',
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True
                )
                
                # Iniciar scheduler
                self.scheduler.start()
                self.is_running = True
                
                logger.info("✅ Campaign Scheduler started successfully")
                
            except Exception as e:
                logger.error(f"Error starting scheduler: {e}")
                self.is_running = False
                raise
    
    def stop(self):
        """Parar o scheduler"""
        with self._lock:
            if not self.is_running:
                logger.warning("Scheduler not running")
                return
            
            try:
                if self.scheduler:
                    self.scheduler.shutdown(wait=True)
                    self.scheduler = None
                
                self.is_running = False
                logger.info("Campaign Scheduler stopped")
                
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
    
    def get_status(self):
        """Obter status do scheduler"""
        return {
            'running': self.is_running,
            'jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0,
            'next_run': self._get_next_run_time()
        }
    
    def _get_next_run_time(self):
        """Obter próximo horário de execução"""
        if not self.scheduler:
            return None
        
        jobs = self.scheduler.get_jobs()
        if not jobs:
            return None
        
        next_run = min(job.next_run_time for job in jobs if job.next_run_time)
        return next_run.isoformat() if next_run else None
    
    def _check_campaigns(self):
        """Verificar e executar campanhas que devem rodar agora"""
        try:
            logger.debug("Checking campaigns for execution...")
            
            # Buscar campanhas ativas
            active_campaigns = WACampaign.query.filter_by(status='active').all()
            
            if not active_campaigns:
                logger.debug("No active campaigns found")
                return
            
            executed_count = 0
            
            for campaign in active_campaigns:
                try:
                    # Verificar se deve executar agora
                    should_execute = self.campaign_service.should_execute_now(campaign)
                    
                    if should_execute:
                        logger.info(f"Executing campaign: {campaign.name} (ID: {campaign.id})")
                        
                        # Executar campanha
                        result = self.campaign_service.execute_campaign(campaign)
                        
                        if result['success']:
                            executed_count += 1
                            logger.info(f"Campaign executed successfully: {campaign.name} - "
                                      f"{result['sent_count']} sent, {result['error_count']} errors")
                        else:
                            logger.error(f"Campaign execution failed: {campaign.name} - {result.get('error')}")
                    
                except Exception as e:
                    logger.error(f"Error checking campaign {campaign.id}: {e}")
                    continue
            
            if executed_count > 0:
                logger.info(f"Campaign check completed: {executed_count} campaigns executed")
            else:
                logger.debug("Campaign check completed: no campaigns executed")
                
        except Exception as e:
            logger.error(f"Error in campaign checker: {e}")
    
    def _cleanup_old_logs(self):
        """Limpar logs antigos (mais de 30 dias)"""
        try:
            from src.admin.models.campaign import WACampaignRun
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Contar logs antigos
            old_logs_count = WACampaignRun.query.filter(
                WACampaignRun.run_at < cutoff_date
            ).count()
            
            if old_logs_count > 0:
                # Deletar logs antigos
                WACampaignRun.query.filter(
                    WACampaignRun.run_at < cutoff_date
                ).delete()
                
                db.session.commit()
                
                logger.info(f"Cleaned up {old_logs_count} old campaign logs")
            else:
                logger.debug("No old logs to clean up")
                
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            db.session.rollback()
    
    def force_check(self):
        """Forçar verificação imediata de campanhas"""
        try:
            logger.info("Force checking campaigns...")
            self._check_campaigns()
            return True
        except Exception as e:
            logger.error(f"Error in force check: {e}")
            return False
    
    def execute_campaign_now(self, campaign_id):
        """Executar campanha específica imediatamente"""
        try:
            campaign = WACampaign.query.get(campaign_id)
            if not campaign:
                return {'success': False, 'error': 'Campaign not found'}
            
            logger.info(f"Force executing campaign: {campaign.name} (ID: {campaign.id})")
            
            result = self.campaign_service.execute_campaign(campaign)
            
            if result['success']:
                logger.info(f"Force execution completed: {campaign.name} - "
                          f"{result['sent_count']} sent, {result['error_count']} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in force execution of campaign {campaign_id}: {e}")
            return {'success': False, 'error': str(e)}

# Instância global do scheduler
campaign_scheduler = CampaignSchedulerService()

def init_campaign_scheduler():
    """Inicializar o scheduler de campanhas"""
    try:
        campaign_scheduler.start()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize campaign scheduler: {e}")
        return False

def stop_campaign_scheduler():
    """Parar o scheduler de campanhas"""
    try:
        campaign_scheduler.stop()
        return True
    except Exception as e:
        logger.error(f"Failed to stop campaign scheduler: {e}")
        return False

