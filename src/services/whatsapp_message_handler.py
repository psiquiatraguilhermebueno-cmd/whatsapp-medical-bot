import logging 
import os
from typing import Dict, Any
from src.services.whatsapp_service import WhatsAppService
from src.services.whatsapp_admin_service import WhatsAppAdminService
from src.services.whatsapp_questionnaire_service import WhatsAppQuestionnaireService
from src.services.whatsapp_scheduler_service import WhatsAppSchedulerService
from src.services.whatsapp_mood_service import WhatsAppMoodService
from src.models.patient import Patient
from src.models.breathing_exercise import BreathingExercise
from src.models.user import db

class WhatsAppMessageHandler:
    """Handler principal para processar mensagens do WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.admin_service = WhatsAppAdminService()
        self.questionnaire_service = WhatsAppQuestionnaireService()
        self.scheduler_service = WhatsAppSchedulerService()
        self.mood_service = WhatsAppMoodService()
        self.logger = logging.getLogger(__name__)
        
        # Número do administrador (configurado via variável de ambiente)
        self.admin_phone = os.getenv('ADMIN_PHONE_NUMBER')
    
    def handle_webhook(self, webhook_data: Dict) -> Dict:
        """
        Processar webhook do WhatsApp
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Resultado do processamento
        """
        try:
            # Processar mensagem
            message_data = self.whatsapp_service.parse_webhook_message(webhook_data)
            if not message_data:
                return {"status": "ignored", "reason": "Invalid webhook data"}
            
            # Marcar mensagem como lida
            if message_data.get('message_id'):
                self.whatsapp_service.mark_message_as_read(message_data['message_id'])
            
            # Extrair informações do usuário
            user_info = {
                "phone_number": message_data.get('from'),
                "name": message_data.get('contact_name', 'Usuário'),
                "message_id": message_data.get('message_id'),
                "timestamp": message_data.get('timestamp')
            }
            
            phone_number = user_info["phone_number"]
            
            # Verificar se é mensagem de texto
            if message_data.get('type') == 'text':
                return self._handle_text_message(phone_number, message_data.get('text', ''), user_info)
            
            # Verificar se é resposta interativa (botão ou lista)
            elif message_data.get('type') == 'interactive':
                return self._handle_interactive_message(phone_number, message_data.get('interactive', {}), user_info)
            
            # Outros tipos de mensagem
            else:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "Desculpe, não consigo processar este tipo de mensagem. Use apenas texto ou os botões fornecidos."
                )
                return {"status": "processed", "action": "unsupported_message_type"}
                
        except Exception as e:
            self.logger.error(f"Erro ao processar webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_text_message(self, phone_number: str, message_text: str, user_info: Dict) -> Dict:
        """Processar mensagem de texto"""
        try:
            # Verificar se é comando administrativo
            if self._is_admin(phone_number):
                return self._handle_admin_command(phone_number, message_text, user_info)
            
            # Verificar comandos básicos
            if message_text.lower() in ['/start', 'oi', 'olá', 'menu']:
                return self._send_welcome_message(phone_number, user_info)
            
            # Para pacientes, resposta padrão
            patient = self._get_or_create_patient(user_info)
            if patient:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "Mensagem recebida! Se você está respondendo a um questionário, use os botões fornecidos."
                )
                return {"status": "processed", "action": "patient_response_received"}
            
            return {"status": "processed", "action": "text_message_handled"}
            
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem de texto: {e}")
            return {"status": "error", "message": str(e)}
    
   def _handle_interactive_message(self, phone_number: str, interactive_data: Dict, user_info: Dict) -> Dict:
    """Processar mensagem interativa (botões/listas)"""
    try:
        # 1) Extrair ID ou título da resposta
        response_id = None
        if interactive_data.get('type') == 'button_reply':
            btn = interactive_data.get('button_reply') or {}
            response_id = btn.get('id') or btn.get('title')
        elif interactive_data.get('type') == 'list_reply':
            lr = interactive_data.get('list_reply') or {}
            response_id = lr.get('id') or lr.get('title')

        if not response_id:
            return {"status": "error", "message": "No response ID or title"}

        # 2) u-ETG: aceitar IDs (slot_XXXX) ou títulos ("07:30", "12:15", "19:00")
        slot_ids = {"slot_0730", "slot_1215", "slot_1900"}
        slot_titles = {"07:30": "slot_0730", "12:15": "slot_1215", "19:00": "slot_1900"}

        normalized = None
        if response_id in slot_ids:
            normalized = response_id
        elif response_id in slot_titles:
            normalized = slot_titles[response_id]

        # 3) Se for confirmação u-ETG, processa e encerra
        if normalized:
            from src.jobs.uetg_scheduler import process_button_click
            patient = self._get_or_create_patient(user_info)
            patient_name = (patient.name if patient else user_info.get("name") or "Paciente")
            ok = process_button_click(normalized, phone_number, patient_name)
            if ok:
                return {"status": "processed", "action": "uetg_slot_confirmed"}
            else:
                self.whatsapp_service.send_text_message(
                    phone_number, "❌ Erro ao confirmar horário. Tente novamente."
                )
                return {"status": "error", "action": "uetg_slot_error"}

        # 4) Não é u-ETG: fluxo normal
        if self._is_admin(phone_number):
            return self._handle_admin_callback(phone_number, response_id, user_info)

        if response_id.startswith('start_questionnaire_') or response_id.startswith('questionnaire_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_questionnaire_callback(phone_number, response_id, patient)

        if response_id.startswith('medication_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_medication_callback(phone_number, response_id, patient)

        if response_id.startswith('mood_') or response_id.startswith('start_mood_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_mood_callback(phone_number, response_id, patient)

        if response_id.startswith('breathing_') or response_id.startswith('start_breathing_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_breathing_callback(phone_number, response_id, patient)

        if response_id.startswith('snooze_') or response_id.startswith('skip_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_reminder_action(phone_number, response_id, patient)

        return {"status": "processed", "action": "interactive_handled"}

    except Exception as e:
        self.logger.error(f"Erro ao processar mensagem interativa: {e}")
        return {"status": "error", "message": str(e)}
    
    def _handle_admin_command(self, phone_number: str, command: str, user_info: Dict) -> Dict:
        """Processar comando administrativo"""
        return self.admin_service.handle_command(phone_number, command, user_info)
    
    def _handle_admin_callback(self, phone_number: str, callback_data: str, user_info: Dict) -> Dict:
        """Processar callback administrativo"""
        return self.admin_service.handle_callback(phone_number, callback_data, user_info)
    
    def _handle_questionnaire_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de questionário"""
        if callback_data.startswith('start_questionnaire_'):
            # Extrair nome da escala
            scale_name = callback_data.replace('start_questionnaire_', '')
            return self.questionnaire_service.start_questionnaire(phone_number, scale_name, patient)
        elif callback_data.startswith('questionnaire_answer_'):
            return self.questionnaire_service.handle_response(phone_number, callback_data, patient)
        else:
            return {"status": "processed", "action": "questionnaire_callback_handled"}
    
    def _handle_medication_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de medicação"""
        return self.scheduler_service.handle_medication_confirmation(phone_number, callback_data, patient)
    
    def _handle_mood_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de humor"""
        if callback_data == 'start_mood_chart':
            return self.mood_service.start_mood_chart(phone_number, patient)
        elif callback_data.startswith('mood_'):
            return self.mood_service.handle_mood_response(phone_number, callback_data, patient)
        else:
            return {"status": "processed", "action": "mood_callback_handled"}
    
    def _handle_breathing_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de exercício de respiração"""
        if callback_data.startswith('start_breathing_'):
            exercise_id = int(callback_data.split('_')[-1])
            return self._start_breathing_exercise(phone_number, exercise_id, patient)
        else:
            return {"status": "processed", "action": "breathing_callback_handled"}
    
    def _handle_reminder_action(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar ações de lembrete (snooze, skip)"""
        if callback_data.startswith('snooze_'):
            return self.scheduler_service.handle_reminder_snooze(phone_number, callback_data, patient)
        elif callback_data.startswith('skip_'):
            return self.scheduler_service.handle_reminder_skip(phone_number, callback_data, patient)
        else:
            return {"status": "processed", "action": "reminder_action_handled"}
    
    def _send_welcome_message(self, phone_number: str, user_info: Dict) -> Dict:
        """Enviar mensagem de boas-vindas"""
        name = user_info.get("name", "")
        
        if self._is_admin(phone_number):
            message = f"""👋 Olá{f', {name}' if name else ''}!

🏥 *Painel Administrativo - Bot de Lembretes Médicos*

Use os comandos abaixo para gerenciar o sistema:

📋 */menu* - Menu principal
👥 */pacientes* - Gerenciar pacientes  
⏰ */lembretes* - Gerenciar lembretes
📊 */relatorios* - Ver relatórios
⚙️ */sistema* - Configurações
📈 */status* - Status rápido

Digite qualquer comando para começar!"""
        else:
            message = f"""👋 Olá{f', {name}' if name else ''}!

🏥 *Bot de Lembretes Médicos*

Sou seu assistente para:
• 📋 Questionários de saúde
• 💊 Lembretes de medicação  
• 😊 Registro de humor
• 🫁 Exercícios de respiração

Aguarde os lembretes automáticos ou digite *menu* para ver as opções disponíveis."""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        return {"status": "sent", "action": "welcome_message_sent"}
    
    def _get_or_create_patient(self, user_info: Dict) -> Patient:
        """Obter ou criar paciente"""
        phone_number = user_info.get("phone_number")
        if not phone_number:
            return None
        
        # Buscar paciente existente
        patient = Patient.query.filter_by(whatsapp_phone=phone_number).first()
        
        if not patient:
            # Criar novo paciente
            patient = Patient(
                name=user_info.get("name", f"Paciente {phone_number[-4:]}"),
                whatsapp_phone=phone_number,
                is_active=True
            )
            db.session.add(patient)
            db.session.commit()
        
        return patient
    
    def _is_admin(self, phone_number: str) -> bool:
        """Verificar se o número é de um administrador"""
        if not self.admin_phone:
            return False
        
        # Suportar múltiplos admins separados por vírgula
        admin_phones = [phone.strip() for phone in self.admin_phone.split(',')]
        return phone_number in admin_phones
    
    def _start_breathing_exercise(self, phone_number: str, exercise_id: int, patient: Patient) -> Dict:
        """Iniciar exercício de respiração"""
        try:
            exercise = BreathingExercise.query.get(exercise_id)
            if not exercise:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "❌ Exercício de respiração não encontrado."
                )
                return {"status": "error", "message": "Exercise not found"}
            
            message = f"""🫁 *{exercise.name}*

{exercise.description}

📝 *Instruções:*
{exercise.instructions}

⏱️ *Duração:* {exercise.duration_minutes} minutos

Vamos começar? Encontre um local confortável e siga as instruções."""
            
            buttons = [
                {"id": f"breathing_start_audio_{exercise_id}", "title": "🎵 Iniciar com áudio"},
                {"id": f"breathing_start_text_{exercise_id}", "title": "📝 Apenas instruções"},
                {"id": "breathing_cancel", "title": "❌ Cancelar"}
            ]
            
            self.whatsapp_service.send_interactive_message(
                phone_number, 
                "Exercício de Respiração", 
                message, 
                buttons
            )
            
            return {"status": "sent", "action": "breathing_exercise_started"}
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar exercício de respiração: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_uetg_slot_callback(self, phone_number: str, response_id: str, patient) -> Dict:
        """Processar clique nos botões de horário u-ETG"""
        try:
            from src.jobs.uetg_scheduler import process_button_click
            
            # Processar o clique do botão
            success = process_button_click(response_id, phone_number, patient.name)
            
            if success:
                return {"status": "processed", "action": "uetg_slot_confirmed"}
            else:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "❌ Erro ao confirmar horário. Tente novamente ou entre em contato."
                )
                return {"status": "error", "action": "uetg_slot_error"}
                
        except Exception as e:
            self.logger.error(f"Erro ao processar confirmação u-ETG: {e}")
            self.whatsapp_service.send_text_message(
                phone_number,
                "❌ Erro interno. Entre em contato com o suporte."
            )
            return {"status": "error", "message": str(e)}
    
    def notify_admin(self, message: str) -> Dict:
        """Enviar notificação para o administrador"""
        if not self.admin_phone:
            self.logger.warning("Admin phone não configurado")
            return {"status": "error", "message": "Admin phone not configured"}
        
        try:
            # Suportar múltiplos admins separados por vírgula
            admin_phones = [phone.strip() for phone in self.admin_phone.split(',')]
            for admin_phone in admin_phones:
                self.whatsapp_service.send_text_message(admin_phone, message)
            
            return {"status": "sent", "action": "admin_notified"}
            
        except Exception as e:
            self.logger.error(f"Erro ao notificar admin: {e}")
            return {"status": "error", "message": str(e)}

