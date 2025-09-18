from typing import Dict, List
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.medication import Medication
from src.models.user import db
from src.services.whatsapp_service import WhatsAppService
from src.services.questionnaire_service import QuestionnaireService
from src.services.medication_service import MedicationService
from src.services.mood_service import MoodService
from datetime import datetime, timedelta, time, date
import threading
import time as time_module

class SchedulerService:
    """Serviço para agendamento e envio automático de lembretes"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.questionnaire_service = QuestionnaireService()
        self.medication_service = MedicationService()
        self.mood_service = MoodService()
        self.running = False
        self.scheduler_thread = None
    
    def start_scheduler(self):
        """Iniciar o agendador"""
        if self.running:
            print("Agendador já está rodando")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("Agendador iniciado com sucesso")
    
    def stop_scheduler(self):
        """Parar o agendador"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        print("Agendador parado")
    
    def _scheduler_loop(self):
        """Loop principal do agendador"""
        while self.running:
            try:
                self._check_and_send_reminders()
                self._check_and_send_medication_reminders()
                self._check_and_send_mood_reminders()
                
                # Aguardar 1 minuto antes da próxima verificação
                time_module.sleep(60)
                
            except Exception as e:
                print(f"Erro no agendador: {e}")
                time_module.sleep(60)  # Aguardar antes de tentar novamente
    
    def _check_and_send_reminders(self):
        """Verificar e enviar lembretes programados"""
        now = datetime.now()
        
        # Buscar lembretes que devem ser enviados
        due_reminders = Reminder.query.filter(
            Reminder.is_active == True,
            Reminder.next_send_date <= now
        ).all()
        
        for reminder in due_reminders:
            try:
                self._send_reminder(reminder)
                self._update_next_send_date(reminder)
            except Exception as e:
                print(f"Erro ao enviar lembrete {reminder.id}: {e}")
    
    def _send_reminder(self, reminder: Reminder):
        """Enviar um lembrete específico"""
        patient = Patient.query.get(reminder.patient_id)
        if not patient:
            print(f"Paciente não encontrado para lembrete {reminder.id}")
            return
        
        if reminder.reminder_type == 'scale':
            self._send_scale_reminder(patient, reminder)
        elif reminder.reminder_type == 'task':
            self._send_task_reminder(patient, reminder)
        elif reminder.reminder_type == 'motivational':
            self._send_motivational_reminder(patient, reminder)
        elif reminder.reminder_type == 'breathing':
            self._send_breathing_reminder(patient, reminder)
        elif reminder.reminder_type == 'mood_chart':
            self._send_mood_chart_reminder(patient, reminder)
    
    def _send_scale_reminder(self, patient: Patient, reminder: Reminder):
        """Enviar lembrete de questionário de escala"""
        message = f"""📋 *Lembrete de Questionário*

Olá {patient.name}! 👋

É hora de responder o questionário **{reminder.title}**.

{reminder.description if reminder.description else ''}

Este questionário ajuda no acompanhamento do seu tratamento. Vamos começar?"""
        
        buttons = [
            {'id': f'start_scale_{reminder.scale_type}', 'title': '📋 Começar agora'},
            {'id': f'delay_reminder_{reminder.id}', 'title': '⏰ Lembrar em 1h'},
            {'id': 'help_questionnaire', 'title': '❓ Preciso de ajuda'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "📋 Questionário Agendado",
            message,
            buttons
        )
        
        print(f"Lembrete de escala enviado para {patient.name}: {reminder.scale_type}")
    
    def _send_task_reminder(self, patient: Patient, reminder: Reminder):
        """Enviar lembrete de tarefa"""
        message = f"""📝 *Lembrete de Tarefa*

Olá {patient.name}! 👋

**{reminder.title}**

{reminder.description if reminder.description else ''}

Por favor, complete esta tarefa e me informe quando terminar."""
        
        buttons = [
            {'id': f'task_completed_{reminder.id}', 'title': '✅ Tarefa concluída'},
            {'id': f'task_help_{reminder.id}', 'title': '❓ Preciso de ajuda'},
            {'id': f'delay_reminder_{reminder.id}', 'title': '⏰ Lembrar depois'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "📝 Tarefa Agendada",
            message,
            buttons
        )
        
        print(f"Lembrete de tarefa enviado para {patient.name}: {reminder.title}")
    
    def _send_motivational_reminder(self, patient: Patient, reminder: Reminder):
        """Enviar mensagem motivacional"""
        message = f"""✨ *Mensagem Motivacional*

Olá {patient.name}! 🌟

{reminder.description if reminder.description else reminder.title}

Lembre-se: você é mais forte do que imagina! 💪

Continue cuidando de si mesmo. Estou aqui para apoiá-lo! 🤗"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        print(f"Mensagem motivacional enviada para {patient.name}")
    
    def _send_breathing_reminder(self, patient: Patient, reminder: Reminder):
        """Enviar lembrete de exercício de respiração"""
        message = f"""🫁 *Hora do Exercício de Respiração*

Olá {patient.name}! 😌

Que tal fazer uma pausa para um exercício de respiração?

Isso pode ajudar a:
• Reduzir o estresse
• Melhorar o foco
• Relaxar o corpo e a mente

Escolha um exercício para começar:"""
        
        buttons = [
            {'id': 'breathing_478', 'title': '🫁 Respiração 4-7-8'},
            {'id': 'breathing_box', 'title': '📦 Respiração Quadrada'},
            {'id': 'breathing_anxiety', 'title': '😰 Anti-Ansiedade'},
            {'id': 'breathing_list', 'title': '📋 Ver todos'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "🫁 Momento de Respirar",
            message,
            buttons
        )
        
        print(f"Lembrete de respiração enviado para {patient.name}")
    
    def _send_mood_chart_reminder(self, patient: Patient, reminder: Reminder):
        """Enviar lembrete de registro de humor"""
        message = f"""😊 *Registro de Humor Diário*

Olá {patient.name}! 📊

Como você está se sentindo hoje?

É importante registrar seu humor diariamente para acompanhar sua evolução.

Vamos fazer o registro de hoje?"""
        
        buttons = [
            {'id': 'start_mood_chart', 'title': '😊 Registrar humor'},
            {'id': 'mood_help', 'title': '❓ Como funciona?'},
            {'id': f'delay_reminder_{reminder.id}', 'title': '⏰ Lembrar depois'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "😊 Registro de Humor",
            message,
            buttons
        )
        
        print(f"Lembrete de humor enviado para {patient.name}")
    
    def _check_and_send_medication_reminders(self):
        """Verificar e enviar lembretes de medicação"""
        now = datetime.now()
        current_time = now.time()
        current_date = now.date()
        
        # Buscar medicações ativas
        medications = Medication.query.filter_by(is_active=True).all()
        
        for medication in medications:
            # Verificar se está dentro do período de tratamento
            if medication.start_date > current_date:
                continue
            if medication.end_date and medication.end_date < current_date:
                continue
            
            # Verificar se é hora de alguma dose
            for scheduled_time_str in medication.times:
                scheduled_time = datetime.strptime(scheduled_time_str, '%H:%M').time()
                
                # Verificar se é o horário (com tolerância de 1 minuto)
                time_diff = abs(
                    (current_time.hour * 60 + current_time.minute) - 
                    (scheduled_time.hour * 60 + scheduled_time.minute)
                )
                
                if time_diff <= 1:  # Tolerância de 1 minuto
                    patient = Patient.query.get(medication.patient_id)
                    if patient:
                        self.medication_service.send_medication_reminder(patient, medication)
    
    def _check_and_send_mood_reminders(self):
        """Verificar e enviar lembretes de humor para pacientes que não registraram hoje"""
        now = datetime.now()
        today = now.date()
        
        # Verificar apenas uma vez por dia (às 20:00)
        if now.hour != 20 or now.minute != 0:
            return
        
        # Buscar pacientes ativos
        patients = Patient.query.filter_by(is_active=True).all()
        
        for patient in patients:
            # Verificar se já registrou humor hoje
            from src.models.mood_chart import MoodChart
            existing_entry = MoodChart.query.filter_by(
                patient_id=patient.id,
                date=today
            ).first()
            
            if not existing_entry:
                # Enviar lembrete de humor
                message = f"""😊 *Lembrete de Humor*

Olá {patient.name}! 🌙

Você ainda não registrou seu humor hoje. 

Que tal fazer isso agora antes de dormir? Leva apenas 2 minutos!"""
                
                buttons = [
                    {'id': 'start_mood_chart', 'title': '😊 Registrar agora'},
                    {'id': 'mood_tomorrow', 'title': '🌅 Amanhã cedo'}
                ]
                
                self.whatsapp_service.send_interactive_message(
                    patient.phone_number,
                    "😊 Registro de Humor",
                    message,
                    buttons
                )
                
                print(f"Lembrete de humor noturno enviado para {patient.name}")
    
    def _update_next_send_date(self, reminder: Reminder):
        """Atualizar próxima data de envio do lembrete"""
        now = datetime.now()
        
        if reminder.frequency == 'daily':
            reminder.next_send_date = now + timedelta(days=1)
        elif reminder.frequency == 'weekly':
            reminder.next_send_date = now + timedelta(weeks=1)
        elif reminder.frequency == 'monthly':
            reminder.next_send_date = now + timedelta(days=30)
        elif reminder.frequency == 'once':
            reminder.is_active = False  # Desativar lembrete único
        elif reminder.frequency == 'custom':
            # Implementar lógica customizada baseada em reminder.custom_schedule
            reminder.next_send_date = self._calculate_custom_next_date(reminder, now)
        
        db.session.commit()
        print(f"Próxima data atualizada para lembrete {reminder.id}: {reminder.next_send_date}")
    
    def _calculate_custom_next_date(self, reminder: Reminder, current_date: datetime) -> datetime:
        """Calcular próxima data para frequência customizada"""
        if not reminder.custom_schedule:
            return current_date + timedelta(days=1)
        
        # Exemplo de implementação para dias da semana
        if 'weekdays' in reminder.custom_schedule:
            weekdays = reminder.custom_schedule['weekdays']  # [0, 1, 2, 3, 4] para seg-sex
            
            next_date = current_date + timedelta(days=1)
            while next_date.weekday() not in weekdays:
                next_date += timedelta(days=1)
            
            # Manter o mesmo horário
            return datetime.combine(
                next_date.date(),
                reminder.scheduled_time
            )
        
        # Padrão: próximo dia
        return current_date + timedelta(days=1)
    
    def create_reminder(self, patient_id: int, reminder_type: str, title: str, 
                       scheduled_time: time, frequency: str = 'daily', 
                       description: str = None, scale_type: str = None,
                       medication_id: int = None, breathing_exercise_id: int = None,
                       custom_schedule: dict = None) -> Reminder:
        """Criar um novo lembrete"""
        
        # Calcular próxima data de envio
        now = datetime.now()
        today = now.date()
        
        # Se o horário de hoje já passou, começar amanhã
        next_send_datetime = datetime.combine(today, scheduled_time)
        if next_send_datetime <= now:
            if frequency == 'daily':
                next_send_datetime += timedelta(days=1)
            elif frequency == 'weekly':
                next_send_datetime += timedelta(days=7)
            elif frequency == 'monthly':
                next_send_datetime += timedelta(days=30)
            elif frequency == 'once':
                next_send_datetime += timedelta(days=1)
        
        reminder = Reminder(
            patient_id=patient_id,
            reminder_type=reminder_type,
            scale_type=scale_type,
            medication_id=medication_id,
            breathing_exercise_id=breathing_exercise_id,
            title=title,
            description=description,
            frequency=frequency,
            scheduled_time=scheduled_time,
            next_send_date=next_send_datetime,
            custom_schedule=custom_schedule
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        print(f"Lembrete criado: {title} para paciente {patient_id}")
        return reminder
    
    def get_due_reminders_count(self) -> int:
        """Obter número de lembretes pendentes"""
        now = datetime.now()
        return Reminder.query.filter(
            Reminder.is_active == True,
            Reminder.next_send_date <= now
        ).count()
    
    def get_scheduler_status(self) -> Dict:
        """Obter status do agendador"""
        return {
            'running': self.running,
            'due_reminders': self.get_due_reminders_count(),
            'total_active_reminders': Reminder.query.filter_by(is_active=True).count(),
            'total_active_medications': Medication.query.filter_by(is_active=True).count()
        }

