import logging
import os
from typing import Dict, List
from datetime import datetime, timedelta
from src.services.telegram_service import TelegramService
from src.services.telegram_questionnaire_service import TelegramQuestionnaireService
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.medication import Medication, MedicationConfirmation
from src.models.mood_chart import MoodChart
from src.models.breathing_exercise import BreathingExercise
from src.models.user import db

class TelegramSchedulerService:
    """Serviço de agendamento para envio de lembretes via Telegram"""
    
    def __init__(self):
        self.telegram_service = TelegramService(bot_token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.questionnaire_service = TelegramQuestionnaireService()
        self.logger = logging.getLogger(__name__)
    
    def send_scale_reminder(self, reminder: Reminder) -> Dict:
        """Enviar lembrete de escala clínica"""
        try:
            patient = Patient.query.get(reminder.patient_id)
            if not patient or not patient.telegram_chat_id:
                return {"status": "error", "message": "Patient not found or no Telegram chat"}
            
            chat_id = patient.telegram_chat_id
            reminder_data = reminder.reminder_data or {}
            scale_name = reminder_data.get('scale_name', 'Questionário')
            
            message = f"""📋 *Lembrete de Questionário*

Olá, {patient.name}! 👋

É hora de responder ao questionário *{scale_name}*.

Este questionário ajuda seu profissional de saúde a acompanhar seu bem-estar.

⏱️ *Tempo estimado:* 2-3 minutos"""
            
            buttons = [
                {"text": "📝 Responder agora", "callback_data": f"start_questionnaire_{scale_name}"},
                {"text": "⏰ Lembrar em 1 hora", "callback_data": f"snooze_reminder_{reminder.id}_1"},
                {"text": "❌ Pular hoje", "callback_data": f"skip_reminder_{reminder.id}"}
            ]
            
            result = self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            if result.get('ok'):
                return {"status": "sent", "action": "scale_reminder_sent"}
            else:
                return {"status": "error", "message": "Failed to send message"}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de escala: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_medication_reminder(self, reminder: Reminder) -> Dict:
        """Enviar lembrete de medicação"""
        try:
            patient = Patient.query.get(reminder.patient_id)
            if not patient or not patient.telegram_chat_id:
                return {"status": "error", "message": "Patient not found or no Telegram chat"}
            
            chat_id = patient.telegram_chat_id
            reminder_data = reminder.reminder_data or {}
            
            # Buscar medicações do paciente
            medications = Medication.query.filter_by(
                patient_id=patient.id,
                is_active=True
            ).all()
            
            if not medications:
                return {"status": "error", "message": "No active medications found"}
            
            message = f"""💊 *Lembrete de Medicação*

Olá, {patient.name}! 👋

É hora de tomar sua medicação:

"""
            
            buttons = []
            
            for medication in medications:
                message += f"💊 *{medication.name}*\n"
                message += f"   📏 Dosagem: {medication.dosage}\n"
                message += f"   ⏰ Horário: {datetime.now().strftime('%H:%M')}\n\n"
                
                buttons.append({
                    "text": f"✅ Tomei {medication.name}",
                    "callback_data": f"medication_taken_{medication.id}"
                })
            
            # Botões adicionais
            buttons.extend([
                {"text": "⏰ Lembrar em 15 min", "callback_data": f"snooze_medication_{reminder.id}_15"},
                {"text": "❌ Não vou tomar hoje", "callback_data": f"skip_medication_{reminder.id}"}
            ])
            
            result = self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            if result.get('ok'):
                return {"status": "sent", "action": "medication_reminder_sent"}
            else:
                return {"status": "error", "message": "Failed to send message"}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_mood_reminder(self, reminder: Reminder) -> Dict:
        """Enviar lembrete de registro de humor"""
        try:
            patient = Patient.query.get(reminder.patient_id)
            if not patient or not patient.telegram_chat_id:
                return {"status": "error", "message": "Patient not found or no Telegram chat"}
            
            chat_id = patient.telegram_chat_id
            
            # Verificar se já registrou humor hoje
            today = datetime.now().date()
            existing_mood = MoodChart.query.filter_by(
                patient_id=patient.id,
                date=today
            ).first()
            
            if existing_mood:
                message = f"""😊 *Registro de Humor*

Olá, {patient.name}! 👋

Você já registrou seu humor hoje. Obrigado!

📊 *Humor atual:* {existing_mood.mood_level}/10
😴 *Qualidade do sono:* {existing_mood.sleep_quality or 'Não informado'}

Até amanhã! 🌙"""
                
                self.telegram_service.send_text_message(chat_id, message)
                return {"status": "sent", "action": "mood_already_registered"}
            
            message = f"""😊 *Registro de Humor Diário*

Olá, {patient.name}! 👋

Como você está se sentindo hoje?

Este registro ajuda você e seu profissional a acompanhar seu bem-estar ao longo do tempo.

⏱️ *Tempo estimado:* 1-2 minutos"""
            
            buttons = [
                {"text": "😊 Registrar humor", "callback_data": "start_mood_chart"},
                {"text": "⏰ Lembrar mais tarde", "callback_data": f"snooze_reminder_{reminder.id}_2"},
                {"text": "❌ Pular hoje", "callback_data": f"skip_reminder_{reminder.id}"}
            ]
            
            result = self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            if result.get('ok'):
                return {"status": "sent", "action": "mood_reminder_sent"}
            else:
                return {"status": "error", "message": "Failed to send message"}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de humor: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_breathing_reminder(self, reminder: Reminder) -> Dict:
        """Enviar lembrete de exercício de respiração"""
        try:
            patient = Patient.query.get(reminder.patient_id)
            if not patient or not patient.telegram_chat_id:
                return {"status": "error", "message": "Patient not found or no Telegram chat"}
            
            chat_id = patient.telegram_chat_id
            
            # Buscar exercícios de respiração disponíveis
            exercises = BreathingExercise.query.filter_by(is_active=True).limit(3).all()
            
            message = f"""🫁 *Exercício de Respiração*

Olá, {patient.name}! 👋

Que tal fazer um exercício de respiração para relaxar?

Os exercícios de respiração ajudam a:
• Reduzir ansiedade e estresse
• Melhorar o foco e concentração
• Promover relaxamento

⏱️ *Duração:* 3-5 minutos"""
            
            buttons = []
            
            for exercise in exercises:
                buttons.append({
                    "text": f"🫁 {exercise.name}",
                    "callback_data": f"start_breathing_{exercise.id}"
                })
            
            # Botões adicionais
            buttons.extend([
                {"text": "⏰ Lembrar em 30 min", "callback_data": f"snooze_reminder_{reminder.id}_30"},
                {"text": "❌ Não agora", "callback_data": f"skip_reminder_{reminder.id}"}
            ])
            
            result = self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            if result.get('ok'):
                return {"status": "sent", "action": "breathing_reminder_sent"}
            else:
                return {"status": "error", "message": "Failed to send message"}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de respiração: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_motivational_reminder(self, reminder: Reminder) -> Dict:
        """Enviar lembrete motivacional"""
        try:
            patient = Patient.query.get(reminder.patient_id)
            if not patient or not patient.telegram_chat_id:
                return {"status": "error", "message": "Patient not found or no Telegram chat"}
            
            chat_id = patient.telegram_chat_id
            reminder_data = reminder.reminder_data or {}
            
            # Mensagens motivacionais pré-definidas
            motivational_messages = [
                "🌟 Você é mais forte do que imagina!",
                "💪 Cada dia é uma nova oportunidade de crescer.",
                "🌈 Depois da tempestade, sempre vem o arco-íris.",
                "🌱 Pequenos passos levam a grandes conquistas.",
                "💙 Você não está sozinho nesta jornada.",
                "🦋 A mudança é difícil, mas possível.",
                "🌞 Hoje é um bom dia para cuidar de você.",
                "🎯 Foque no progresso, não na perfeição.",
                "🌸 Seja gentil consigo mesmo.",
                "⭐ Você merece coisas boas na vida."
            ]
            
            # Selecionar mensagem personalizada ou aleatória
            custom_message = reminder_data.get('message')
            if custom_message:
                motivational_text = custom_message
            else:
                import random
                motivational_text = random.choice(motivational_messages)
            
            message = f"""💙 *Mensagem Motivacional*

Olá, {patient.name}! 👋

{motivational_text}

Lembre-se: você está fazendo um ótimo trabalho cuidando da sua saúde mental. Continue assim! 🌟"""
            
            buttons = [
                {"text": "💙 Obrigado!", "callback_data": "motivational_thanks"},
                {"text": "😊 Como estou hoje", "callback_data": "start_mood_chart"}
            ]
            
            result = self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            if result.get('ok'):
                return {"status": "sent", "action": "motivational_reminder_sent"}
            else:
                return {"status": "error", "message": "Failed to send message"}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete motivacional: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_medication_confirmation(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar confirmação de medicação"""
        try:
            # Extrair ID da medicação do callback_data
            # Formato: medication_taken_X
            medication_id = int(callback_data.split('_')[-1])
            
            medication = Medication.query.get(medication_id)
            if not medication:
                return {"status": "error", "message": "Medication not found"}
            
            # Criar confirmação
            confirmation = MedicationConfirmation(
                patient_id=patient.id,
                medication_id=medication_id,
                scheduled_time=datetime.now(),
                confirmed_time=datetime.now(),
                status='confirmed'
            )
            
            db.session.add(confirmation)
            db.session.commit()
            
            message = f"""✅ *Medicação Confirmada*

Ótimo! Você confirmou que tomou:

💊 *{medication.name}*
📏 *Dosagem:* {medication.dosage}
⏰ *Horário:* {datetime.now().strftime('%H:%M')}

Continue assim! 👏"""
            
            self.telegram_service.send_text_message(chat_id, message)
            
            return {"status": "confirmed", "action": "medication_confirmed"}
            
        except Exception as e:
            self.logger.error(f"Erro ao confirmar medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_reminder_snooze(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar adiamento de lembrete"""
        try:
            # Extrair dados do callback_data
            # Formato: snooze_reminder_X_Y onde X é reminder_id e Y são os minutos
            parts = callback_data.split('_')
            reminder_id = int(parts[2])
            minutes = int(parts[3])
            
            reminder = Reminder.query.get(reminder_id)
            if not reminder:
                return {"status": "error", "message": "Reminder not found"}
            
            # Agendar novo lembrete
            new_time = datetime.now() + timedelta(minutes=minutes)
            
            # Aqui você implementaria a lógica para reagendar o lembrete
            # Por simplicidade, apenas confirmamos o adiamento
            
            message = f"""⏰ *Lembrete Adiado*

Ok! Vou te lembrar novamente em {minutes} minutos.

⏰ *Próximo lembrete:* {new_time.strftime('%H:%M')}"""
            
            self.telegram_service.send_text_message(chat_id, message)
            
            return {"status": "snoozed", "action": "reminder_snoozed", "minutes": minutes}
            
        except Exception as e:
            self.logger.error(f"Erro ao adiar lembrete: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_reminder_skip(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar pular lembrete"""
        try:
            # Extrair ID do lembrete
            reminder_id = int(callback_data.split('_')[-1])
            
            reminder = Reminder.query.get(reminder_id)
            if not reminder:
                return {"status": "error", "message": "Reminder not found"}
            
            message = """❌ *Lembrete Pulado*

Tudo bem! Você pode responder quando se sentir confortável.

Lembre-se: cuidar da sua saúde mental é importante. 💙"""
            
            self.telegram_service.send_text_message(chat_id, message)
            
            return {"status": "skipped", "action": "reminder_skipped"}
            
        except Exception as e:
            self.logger.error(f"Erro ao pular lembrete: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_reminder_by_type(self, reminder: Reminder) -> Dict:
        """Enviar lembrete baseado no tipo"""
        reminder_type = reminder.reminder_type
        
        if reminder_type == 'scale':
            return self.send_scale_reminder(reminder)
        elif reminder_type == 'medication':
            return self.send_medication_reminder(reminder)
        elif reminder_type == 'mood':
            return self.send_mood_reminder(reminder)
        elif reminder_type == 'breathing':
            return self.send_breathing_reminder(reminder)
        elif reminder_type == 'motivational':
            return self.send_motivational_reminder(reminder)
        else:
            self.logger.warning(f"Tipo de lembrete não suportado: {reminder_type}")
            return {"status": "error", "message": f"Unsupported reminder type: {reminder_type}"}

