import logging
import os
from typing import Dict, List
from datetime import datetime, timedelta
from src.services.whatsapp_service import WhatsAppService
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.medication import Medication, MedicationConfirmation
from src.models.breathing_exercise import BreathingExercise
from src.models.user import db

class WhatsAppSchedulerService:
    """Serviço de agendamento para enviar lembretes automáticos via WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.logger = logging.getLogger(__name__)
    
    def send_questionnaire_reminder(self, patient: Patient, scale_name: str, reminder: Reminder) -> Dict:
        """Enviar lembrete de questionário"""
        try:
            message = f"""📋 *Lembrete de Questionário*

Olá, {patient.name}! 

É hora de responder o questionário *{scale_name}*.

Este questionário ajuda seu profissional de saúde a acompanhar seu progresso e bem-estar.

⏱️ *Tempo estimado:* 2-3 minutos"""
            
            buttons = [
                {"id": f"start_questionnaire_{scale_name}", "title": "📝 Responder Agora"},
                {"id": f"snooze_reminder_{reminder.id}", "title": "⏰ Lembrar em 1h"},
                {"id": f"skip_reminder_{reminder.id}", "title": "⏭️ Pular Hoje"}
            ]
            
            result = self.whatsapp_service.send_interactive_message(
                patient.whatsapp_phone,
                "Lembrete de Questionário",
                message,
                buttons
            )
            
            if result.get('success'):
                return {"status": "sent", "action": "questionnaire_reminder_sent"}
            else:
                return {"status": "error", "message": result.get('error', 'Unknown error')}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de questionário: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_medication_reminder(self, patient: Patient, medication: Medication, reminder: Reminder) -> Dict:
        """Enviar lembrete de medicação"""
        try:
            message = f"""💊 *Lembrete de Medicação*

Olá, {patient.name}!

É hora de tomar sua medicação:

💊 *{medication.name}*
📏 *Dosagem:* {medication.dosage}
🕐 *Horário:* {medication.time.strftime('%H:%M')}

"""
            
            if medication.instructions:
                message += f"📝 *Instruções:* {medication.instructions}\n\n"
            
            message += "Por favor, confirme quando tomar a medicação:"
            
            buttons = [
                {"id": f"medication_taken_{medication.id}", "title": "✅ Tomei"},
                {"id": f"medication_snooze_{medication.id}", "title": "⏰ Lembrar em 30min"},
                {"id": f"medication_skip_{medication.id}", "title": "❌ Não vou tomar"}
            ]
            
            result = self.whatsapp_service.send_interactive_message(
                patient.whatsapp_phone,
                "Lembrete de Medicação",
                message,
                buttons
            )
            
            if result.get('success'):
                return {"status": "sent", "action": "medication_reminder_sent"}
            else:
                return {"status": "error", "message": result.get('error', 'Unknown error')}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_mood_reminder(self, patient: Patient, reminder: Reminder) -> Dict:
        """Enviar lembrete de registro de humor"""
        try:
            message = f"""😊 *Lembrete de Registro de Humor*

Olá, {patient.name}!

Como você está se sentindo hoje?

O registro diário de humor ajuda seu profissional de saúde a entender melhor seus padrões e ajustar o tratamento.

⏱️ *Tempo estimado:* 1-2 minutos"""
            
            buttons = [
                {"id": "start_mood_chart", "title": "😊 Registrar Humor"},
                {"id": f"snooze_reminder_{reminder.id}", "title": "⏰ Lembrar em 2h"},
                {"id": f"skip_reminder_{reminder.id}", "title": "⏭️ Pular Hoje"}
            ]
            
            result = self.whatsapp_service.send_interactive_message(
                patient.whatsapp_phone,
                "Registro de Humor",
                message,
                buttons
            )
            
            if result.get('success'):
                return {"status": "sent", "action": "mood_reminder_sent"}
            else:
                return {"status": "error", "message": result.get('error', 'Unknown error')}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de humor: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_breathing_reminder(self, patient: Patient, reminder: Reminder) -> Dict:
        """Enviar lembrete de exercício de respiração"""
        try:
            message = f"""🫁 *Lembrete de Exercício de Respiração*

Olá, {patient.name}!

Que tal fazer um exercício de respiração para relaxar?

Os exercícios de respiração ajudam a:
• Reduzir ansiedade e estresse
• Melhorar o foco e concentração
• Promover relaxamento

⏱️ *Duração:* 3-15 minutos"""
            
            buttons = [
                {"id": "breathing_menu", "title": "🫁 Ver Exercícios"},
                {"id": f"snooze_reminder_{reminder.id}", "title": "⏰ Lembrar em 1h"},
                {"id": f"skip_reminder_{reminder.id}", "title": "⏭️ Pular Hoje"}
            ]
            
            result = self.whatsapp_service.send_interactive_message(
                patient.whatsapp_phone,
                "Exercício de Respiração",
                message,
                buttons
            )
            
            if result.get('success'):
                return {"status": "sent", "action": "breathing_reminder_sent"}
            else:
                return {"status": "error", "message": result.get('error', 'Unknown error')}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar lembrete de respiração: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_motivational_message(self, patient: Patient, message_text: str, reminder: Reminder) -> Dict:
        """Enviar mensagem motivacional"""
        try:
            message = f"""💚 *Mensagem Motivacional*

Olá, {patient.name}!

{message_text}

Lembre-se: você está no caminho certo e cada pequeno passo importa! 🌟

Continue cuidando bem de você."""
            
            result = self.whatsapp_service.send_text_message(
                patient.whatsapp_phone,
                message
            )
            
            if result.get('success'):
                return {"status": "sent", "action": "motivational_message_sent"}
            else:
                return {"status": "error", "message": result.get('error', 'Unknown error')}
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem motivacional: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_medication_confirmation(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar confirmação de medicação"""
        try:
            if callback_data.startswith('medication_taken_'):
                medication_id = int(callback_data.split('_')[-1])
                return self._confirm_medication_taken(phone_number, medication_id, patient)
            
            elif callback_data.startswith('medication_snooze_'):
                medication_id = int(callback_data.split('_')[-1])
                return self._snooze_medication_reminder(phone_number, medication_id, patient)
            
            elif callback_data.startswith('medication_skip_'):
                medication_id = int(callback_data.split('_')[-1])
                return self._skip_medication(phone_number, medication_id, patient)
            
            else:
                return {"status": "error", "message": "Invalid medication callback"}
                
        except Exception as e:
            self.logger.error(f"Erro ao processar confirmação de medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def _confirm_medication_taken(self, phone_number: str, medication_id: int, patient: Patient) -> Dict:
        """Confirmar que medicação foi tomada"""
        try:
            medication = Medication.query.get(medication_id)
            if not medication:
                return {"status": "error", "message": "Medication not found"}
            
            # Registrar confirmação
            confirmation = MedicationConfirmation(
                patient_id=patient.id,
                medication_id=medication_id,
                taken_at=datetime.now(),
                status='taken'
            )
            
            db.session.add(confirmation)
            db.session.commit()
            
            message = f"""✅ *Medicação Confirmada*

Obrigado por confirmar, {patient.name}!

💊 *{medication.name}* - Registrado às {datetime.now().strftime('%H:%M')}

Continue mantendo sua rotina de medicação em dia! 👏"""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            
            return {"status": "confirmed", "action": "medication_confirmed"}
            
        except Exception as e:
            self.logger.error(f"Erro ao confirmar medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def _snooze_medication_reminder(self, phone_number: str, medication_id: int, patient: Patient) -> Dict:
        """Adiar lembrete de medicação"""
        try:
            message = """⏰ *Lembrete Adiado*

Ok! Vou te lembrar novamente em 30 minutos.

Não se esqueça da sua medicação! 💊"""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            
            # TODO: Implementar reagendamento automático
            
            return {"status": "snoozed", "action": "medication_snoozed"}
            
        except Exception as e:
            self.logger.error(f"Erro ao adiar medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def _skip_medication(self, phone_number: str, medication_id: int, patient: Patient) -> Dict:
        """Pular medicação"""
        try:
            medication = Medication.query.get(medication_id)
            if not medication:
                return {"status": "error", "message": "Medication not found"}
            
            # Registrar como pulada
            confirmation = MedicationConfirmation(
                patient_id=patient.id,
                medication_id=medication_id,
                taken_at=datetime.now(),
                status='skipped'
            )
            
            db.session.add(confirmation)
            db.session.commit()
            
            message = f"""⚠️ *Medicação Pulada*

Registrado que você não tomará *{medication.name}* hoje.

Se tiver dúvidas sobre sua medicação, converse com seu profissional de saúde.

💡 *Lembre-se:* A aderência ao tratamento é importante para sua saúde."""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            
            # Notificar administrador sobre medicação pulada
            self._notify_admin_skipped_medication(patient, medication)
            
            return {"status": "skipped", "action": "medication_skipped"}
            
        except Exception as e:
            self.logger.error(f"Erro ao pular medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_reminder_snooze(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar adiamento de lembrete"""
        try:
            reminder_id = int(callback_data.split('_')[-1])
            
            message = """⏰ *Lembrete Adiado*

Ok! Vou te lembrar novamente mais tarde.

Obrigado por manter seus cuidados em dia! 👍"""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            
            # TODO: Implementar reagendamento automático
            
            return {"status": "snoozed", "action": "reminder_snoozed"}
            
        except Exception as e:
            self.logger.error(f"Erro ao adiar lembrete: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_reminder_skip(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar pular lembrete"""
        try:
            reminder_id = int(callback_data.split('_')[-1])
            
            message = """⏭️ *Lembrete Pulado*

Tudo bem! Você pode responder quando se sentir confortável.

Estamos aqui para apoiar você no seu ritmo. 💚"""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            
            return {"status": "skipped", "action": "reminder_skipped"}
            
        except Exception as e:
            self.logger.error(f"Erro ao pular lembrete: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_breathing_exercises_menu(self, phone_number: str, patient: Patient) -> Dict:
        """Enviar menu de exercícios de respiração"""
        try:
            exercises = BreathingExercise.query.filter_by(is_active=True).all()
            
            if not exercises:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "❌ Nenhum exercício de respiração disponível no momento."
                )
                return {"status": "error", "message": "No exercises available"}
            
            message = """🫁 *Exercícios de Respiração*

Escolha um exercício para começar:"""
            
            # Preparar seções para lista
            sections = [{
                "title": "Exercícios Disponíveis",
                "rows": [
                    {
                        "id": f"start_breathing_{exercise.id}",
                        "title": exercise.name,
                        "description": f"{exercise.duration_minutes}min - {exercise.description[:50]}..."
                    }
                    for exercise in exercises[:10]  # Máximo 10 exercícios
                ]
            }]
            
            self.whatsapp_service.send_list_message(
                phone_number,
                "Exercícios de Respiração",
                message,
                "Escolher Exercício",
                sections
            )
            
            return {"status": "sent", "action": "breathing_menu_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar menu de respiração: {e}")
            return {"status": "error", "message": str(e)}
    
    def _notify_admin_skipped_medication(self, patient: Patient, medication: Medication) -> None:
        """Notificar administrador sobre medicação pulada"""
        try:
            admin_phone = os.getenv('ADMIN_PHONE_NUMBER')
            if not admin_phone:
                return
            
            message = f"""⚠️ *Medicação Pulada*

👤 *Paciente:* {patient.name}
💊 *Medicação:* {medication.name}
🕐 *Horário previsto:* {medication.time.strftime('%H:%M')}
📅 *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

💡 *Sugestão:* Considere conversar com o paciente sobre a importância da aderência ao tratamento."""
            
            # Enviar para todos os admins
            admin_phones = [phone.strip() for phone in admin_phone.split(',')]
            for admin in admin_phones:
                self.whatsapp_service.send_text_message(admin, message)
                
        except Exception as e:
            self.logger.error(f"Erro ao notificar admin sobre medicação pulada: {e}")

