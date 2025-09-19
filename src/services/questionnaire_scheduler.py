"""
Integração com scheduler para envio automático de questionários
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from src.models.patient import Patient
from src.models.schedule import Schedule
from src.routes.whatsapp import start_questionnaire_for_patient

logger = logging.getLogger(__name__)

class QuestionnaireScheduler:
    """Gerencia agendamento automático de questionários"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Scheduler de questionários iniciado")
    
    def schedule_patient_questionnaires(self, patient_id: int):
        """Agenda questionários para um paciente"""
        try:
            patient = Patient.query.get(patient_id)
            if not patient:
                logger.error(f"Paciente {patient_id} não encontrado")
                return False
            
            schedules = Schedule.query.filter_by(patient_id=patient_id, active=True).all()
            
            for schedule in schedules:
                self._schedule_questionnaire(patient, schedule)
            
            logger.info(f"Questionários agendados para paciente {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao agendar questionários: {e}")
            return False
    
    def _schedule_questionnaire(self, patient: Patient, schedule: Schedule):
        """Agenda questionário específico"""
        try:
            job_id = f"patient_{patient.id}_{schedule.protocol_type}"
            
            # Remove job anterior se existir
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Calcula próxima execução
            next_run = self._calculate_next_run(schedule)
            
            if schedule.frequency == 'daily':
                self.scheduler.add_job(
                    func=self._send_questionnaire,
                    trigger='cron',
                    hour=int(schedule.time.split(':')[0]),
                    minute=int(schedule.time.split(':')[1]),
                    args=[patient.id, schedule.protocol_type],
                    id=job_id,
                    replace_existing=True
                )
            elif schedule.frequency == 'weekly':
                self.scheduler.add_job(
                    func=self._send_questionnaire,
                    trigger='cron',
                    day_of_week=0,  # Segunda-feira
                    hour=int(schedule.time.split(':')[0]),
                    minute=int(schedule.time.split(':')[1]),
                    args=[patient.id, schedule.protocol_type],
                    id=job_id,
                    replace_existing=True
                )
            elif schedule.frequency == 'monthly':
                self.scheduler.add_job(
                    func=self._send_questionnaire,
                    trigger='cron',
                    day=1,  # Primeiro dia do mês
                    hour=int(schedule.time.split(':')[0]),
                    minute=int(schedule.time.split(':')[1]),
                    args=[patient.id, schedule.protocol_type],
                    id=job_id,
                    replace_existing=True
                )
            elif schedule.frequency == 'random':
                # Para u-ETG: envio aleatório
                self._schedule_random_questionnaire(patient.id, schedule)
            
            logger.info(f"Questionário {schedule.protocol_type} agendado para paciente {patient.id}")
            
        except Exception as e:
            logger.error(f"Erro ao agendar questionário específico: {e}")
    
    def _schedule_random_questionnaire(self, patient_id: int, schedule: Schedule):
        """Agenda questionário com horário aleatório (u-ETG)"""
        try:
            import random
            
            # Gera horário aleatório entre 7h e 22h
            random_hour = random.randint(7, 22)
            random_minute = random.randint(0, 59)
            
            job_id = f"patient_{patient_id}_random_{schedule.protocol_type}"
            
            self.scheduler.add_job(
                func=self._send_questionnaire,
                trigger='cron',
                hour=random_hour,
                minute=random_minute,
                args=[patient_id, schedule.protocol_type],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"u-ETG agendado aleatoriamente para {random_hour:02d}:{random_minute:02d}")
            
        except Exception as e:
            logger.error(f"Erro ao agendar questionário aleatório: {e}")
    
    def _send_questionnaire(self, patient_id: int, questionnaire_type: str):
        """Envia questionário para paciente"""
        try:
            success = start_questionnaire_for_patient(patient_id, questionnaire_type)
            
            if success:
                logger.info(f"Questionário {questionnaire_type} enviado para paciente {patient_id}")
            else:
                logger.error(f"Falha ao enviar questionário {questionnaire_type} para paciente {patient_id}")
            
            # Reagenda próximo envio se necessário
            self._reschedule_if_needed(patient_id, questionnaire_type)
            
        except Exception as e:
            logger.error(f"Erro ao enviar questionário agendado: {e}")
    
    def _reschedule_if_needed(self, patient_id: int, questionnaire_type: str):
        """Reagenda questionário se necessário"""
        try:
            # Para questionários aleatórios, reagenda para próximo dia
            if questionnaire_type == 'uetg':
                schedule = Schedule.query.filter_by(
                    patient_id=patient_id,
                    protocol_type=questionnaire_type,
                    active=True
                ).first()
                
                if schedule and schedule.frequency == 'random':
                    # Reagenda para amanhã em horário aleatório
                    tomorrow = datetime.now() + timedelta(days=1)
                    self._schedule_random_questionnaire(patient_id, schedule)
            
        except Exception as e:
            logger.error(f"Erro ao reagendar questionário: {e}")
    
    def _calculate_next_run(self, schedule: Schedule) -> datetime:
        """Calcula próxima execução do questionário"""
        now = datetime.now()
        time_parts = schedule.time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if schedule.frequency == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif schedule.frequency == 'weekly':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = 0 - now.weekday()  # Segunda-feira
            if days_ahead <= 0:
                days_ahead += 7
            next_run += timedelta(days=days_ahead)
        elif schedule.frequency == 'monthly':
            next_run = now.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        else:
            next_run = now + timedelta(hours=1)
        
        return next_run
    
    def stop(self):
        """Para o scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler de questionários parado")

# Instância global do scheduler
questionnaire_scheduler = QuestionnaireScheduler()
