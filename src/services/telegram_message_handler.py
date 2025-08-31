import logging
import os
from typing import Dict, Any
from src.services.telegram_service import TelegramService
from src.services.telegram_admin_service import TelegramAdminService
from src.services.telegram_questionnaire_service import TelegramQuestionnaireService
from src.services.telegram_scheduler_service import TelegramSchedulerService
from src.services.telegram_mood_service import TelegramMoodService
from src.models.patient import Patient
from src.models.breathing_exercise import BreathingExercise
from src.models.user import db

class TelegramMessageHandler:
    """Handler principal para processar mensagens do Telegram"""
    
    def __init__(self):
        self.telegram_service = TelegramService(bot_token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.admin_service = TelegramAdminService()
        self.questionnaire_service = TelegramQuestionnaireService()
        self.scheduler_service = TelegramSchedulerService()
        self.mood_service = TelegramMoodService()
        self.logger = logging.getLogger(__name__)
        
        # Número do administrador (configurado via variável de ambiente)
        self.admin_chat_id = os.getenv('ADMIN_CHAT_ID')
    
    def handle_update(self, update: Dict) -> Dict:
        """
        Processar atualização do Telegram
        
        Args:
            update: Atualização recebida do Telegram
            
        Returns:
            Resultado do processamento
        """
        try:
            # Extrair informações do usuário
            user_info = self.telegram_service.extract_user_info(update)
            chat_id = user_info.get('chat_id')
            
            if not chat_id:
                self.logger.warning("Chat ID não encontrado na atualização")
                return {"status": "error", "message": "Chat ID not found"}
            
            # Verificar se é mensagem de texto
            if "message" in update:
                return self._handle_text_message(update, user_info)
            
            # Verificar se é callback query (clique em botão)
            elif "callback_query" in update:
                return self._handle_callback_query(update, user_info)
            
            else:
                self.logger.warning(f"Tipo de atualização não suportado: {update}")
                return {"status": "ignored", "message": "Update type not supported"}
                
        except Exception as e:
            self.logger.error(f"Erro ao processar atualização: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_text_message(self, update: Dict, user_info: Dict) -> Dict:
        """Processar mensagem de texto"""
        message = update["message"]
        text = message.get("text", "")
        chat_id = user_info["chat_id"]
        
        self.logger.info(f"Mensagem de texto recebida de {chat_id}: {text}")
        
        # Verificar se é comando administrativo
        if self._is_admin(chat_id):
            if text.startswith('/'):
                return self._handle_admin_command(chat_id, text, user_info)
            else:
                return self._handle_admin_text(chat_id, text, user_info)
        
        # Verificar se é comando geral
        if text.startswith('/'):
            return self._handle_user_command(chat_id, text, user_info)
        
        # Verificar se paciente está em conversa ativa
        patient = self._get_or_create_patient(user_info)
        if patient:
            return self._handle_patient_response(chat_id, text, patient)
        
        # Mensagem de boas-vindas para novos usuários
        return self._send_welcome_message(chat_id, user_info)
    
    def _handle_callback_query(self, update: Dict, user_info: Dict) -> Dict:
        """Processar callback query (clique em botão)"""
        callback_query = update["callback_query"]
        callback_data = callback_query.get("data", "")
        chat_id = user_info["chat_id"]
        callback_query_id = callback_query["id"]
        
        self.logger.info(f"Callback query recebido de {chat_id}: {callback_data}")
        
        # Responder ao callback query
        self.telegram_service.answer_callback_query(callback_query_id)
        
        # Verificar se é ação administrativa
        if self._is_admin(chat_id):
            return self._handle_admin_callback(chat_id, callback_data, user_info)
        
        # Verificar se é resposta de questionário
        if callback_data.startswith('questionnaire_') or callback_data.startswith('start_questionnaire_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_questionnaire_callback(chat_id, callback_data, patient)
        
        # Verificar se é confirmação de medicação
        if callback_data.startswith('medication_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_medication_callback(chat_id, callback_data, patient)
        
        # Verificar se é registro de humor
        if callback_data.startswith('mood_') or callback_data.startswith('start_mood_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_mood_callback(chat_id, callback_data, patient)
        
        # Verificar se é exercício de respiração
        if callback_data.startswith('breathing_') or callback_data.startswith('start_breathing_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_breathing_callback(chat_id, callback_data, patient)
        
        # Verificar se é ação de lembrete (snooze, skip)
        if callback_data.startswith('snooze_') or callback_data.startswith('skip_'):
            patient = self._get_or_create_patient(user_info)
            if patient:
                return self._handle_reminder_action(chat_id, callback_data, patient)
        
        return {"status": "processed", "action": "callback_handled"}
    
    def _handle_admin_command(self, chat_id: str, command: str, user_info: Dict) -> Dict:
        """Processar comando administrativo"""
        return self.admin_service.handle_command(chat_id, command, user_info)
    
    def _handle_admin_text(self, chat_id: str, text: str, user_info: Dict) -> Dict:
        """Processar texto administrativo"""
        return self.admin_service.handle_text(chat_id, text, user_info)
    
    def _handle_admin_callback(self, chat_id: str, callback_data: str, user_info: Dict) -> Dict:
        """Processar callback administrativo"""
        return self.admin_service.handle_callback(chat_id, callback_data, user_info)
    
    def _handle_user_command(self, chat_id: str, command: str, user_info: Dict) -> Dict:
        """Processar comando de usuário comum"""
        if command == '/start':
            return self._send_welcome_message(chat_id, user_info)
        elif command == '/help' or command == '/ajuda':
            return self._send_help_message(chat_id)
        elif command == '/status':
            return self._send_user_status(chat_id, user_info)
        else:
            self.telegram_service.send_text_message(
                chat_id,
                "Comando não reconhecido. Digite /help para ver os comandos disponíveis."
            )
            return {"status": "processed", "action": "unknown_command"}
    
    def _handle_patient_response(self, chat_id: str, text: str, patient: Patient) -> Dict:
        """Processar resposta de paciente"""
        # Aqui seria implementada a lógica para processar respostas livres
        # Por enquanto, apenas confirma o recebimento
        self.telegram_service.send_text_message(
            chat_id,
            "Mensagem recebida! Se você está respondendo a um questionário, use os botões fornecidos."
        )
        return {"status": "processed", "action": "patient_response_received"}
    
    def _handle_questionnaire_callback(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de questionário"""
        if callback_data.startswith('start_questionnaire_'):
            # Extrair nome da escala
            scale_name = callback_data.replace('start_questionnaire_', '')
            return self.questionnaire_service.start_questionnaire(chat_id, scale_name, patient)
        elif callback_data.startswith('questionnaire_answer_'):
            return self.questionnaire_service.handle_response(chat_id, callback_data, patient)
        else:
            return {"status": "processed", "action": "questionnaire_callback_handled"}
    
    def _handle_medication_callback(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de medicação"""
        return self.scheduler_service.handle_medication_confirmation(chat_id, callback_data, patient)
    
    def _handle_mood_callback(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de humor"""
        if callback_data == 'start_mood_chart':
            return self.mood_service.start_mood_chart(chat_id, patient)
        elif callback_data.startswith('mood_'):
            return self.mood_service.handle_mood_response(chat_id, callback_data, patient)
        else:
            return {"status": "processed", "action": "mood_callback_handled"}
    
    def _handle_breathing_callback(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar callback de exercício de respiração"""
        if callback_data.startswith('start_breathing_'):
            exercise_id = int(callback_data.split('_')[-1])
            return self._start_breathing_exercise(chat_id, exercise_id, patient)
        else:
            return {"status": "processed", "action": "breathing_callback_handled"}
    
    def _handle_reminder_action(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar ações de lembrete (snooze, skip)"""
        if callback_data.startswith('snooze_'):
            return self.scheduler_service.handle_reminder_snooze(chat_id, callback_data, patient)
        elif callback_data.startswith('skip_'):
            return self.scheduler_service.handle_reminder_skip(chat_id, callback_data, patient)
        else:
            return {"status": "processed", "action": "reminder_action_handled"}
    
    def _send_welcome_message(self, chat_id: str, user_info: Dict) -> Dict:
        """Enviar mensagem de boas-vindas"""
        name = user_info.get('first_name', 'usuário')
        
        message = f"""Olá, {name}! 👋

Bem-vindo ao *Bot de Lembretes Médicos*!

Eu sou seu assistente para:
🔹 Lembretes de medicação
🔹 Questionários de saúde mental
🔹 Registro de humor
🔹 Exercícios de respiração

Para começar, seu profissional de saúde precisa cadastrá-lo no sistema.

*Comandos disponíveis:*
/help - Mostrar ajuda
/status - Ver seu status no sistema"""
        
        self.telegram_service.send_text_message(chat_id, message)
        return {"status": "sent", "action": "welcome_message_sent"}
    
    def _send_help_message(self, chat_id: str) -> Dict:
        """Enviar mensagem de ajuda"""
        message = """*Ajuda - Bot de Lembretes Médicos* 🏥

*Comandos disponíveis:*
/start - Iniciar conversa
/help - Mostrar esta ajuda
/status - Ver seu status no sistema

*Como funciona:*
• Seu profissional de saúde cadastra você no sistema
• Você receberá lembretes automáticos
• Responda aos questionários usando os botões
• Confirme medicações quando solicitado
• Registre seu humor diariamente

*Dúvidas?*
Entre em contato com seu profissional de saúde."""
        
        self.telegram_service.send_text_message(chat_id, message)
        return {"status": "sent", "action": "help_message_sent"}
    
    def _send_user_status(self, chat_id: str, user_info: Dict) -> Dict:
        """Enviar status do usuário"""
        patient = Patient.query.filter_by(telegram_chat_id=chat_id).first()
        
        if patient:
            message = f"""*Seu Status no Sistema* 📊

👤 *Nome:* {patient.name}
📱 *Chat ID:* {chat_id}
✅ *Status:* {'Ativo' if patient.is_active else 'Inativo'}
📅 *Cadastrado em:* {patient.created_at.strftime('%d/%m/%Y')}

*Lembretes ativos:* Em breve...
*Última resposta:* Em breve..."""
        else:
            message = f"""*Seu Status no Sistema* 📊

❌ *Você ainda não está cadastrado no sistema.*

Para ser cadastrado, solicite ao seu profissional de saúde que adicione seu chat ID: `{chat_id}`"""
        
        self.telegram_service.send_text_message(chat_id, message)
        return {"status": "sent", "action": "status_message_sent"}
    
    def _get_or_create_patient(self, user_info: Dict) -> Patient:
        """Obter ou criar paciente baseado nas informações do usuário"""
        chat_id = user_info["chat_id"]
        
        # Buscar paciente existente
        patient = Patient.query.filter_by(telegram_chat_id=chat_id).first()
        
        if not patient:
            # Criar paciente temporário (será ativado pelo admin)
            patient = Patient(
                name=user_info.get('full_name', f"Usuário {chat_id}"),
                telegram_chat_id=chat_id,
                telegram_username=user_info.get('username'),
                is_active=False  # Inativo até ser aprovado pelo admin
            )
            db.session.add(patient)
            db.session.commit()
        
        return patient
    
    def _is_admin(self, chat_id: str) -> bool:
        """Verificar se o usuário é administrador"""
        if not self.admin_chat_id:
            return False
        
        # Suportar múltiplos admins separados por vírgula
        admin_ids = [id.strip() for id in self.admin_chat_id.split(',')]
        return chat_id in admin_ids
    
    def _start_breathing_exercise(self, chat_id: str, exercise_id: int, patient: Patient) -> Dict:
        """Iniciar exercício de respiração"""
        try:
            exercise = BreathingExercise.query.get(exercise_id)
            if not exercise:
                self.telegram_service.send_text_message(
                    chat_id,
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
                {"text": "🎵 Iniciar com áudio", "callback_data": f"breathing_start_audio_{exercise_id}"},
                {"text": "📝 Apenas instruções", "callback_data": f"breathing_start_text_{exercise_id}"},
                {"text": "❌ Cancelar", "callback_data": "breathing_cancel"}
            ]
            
            self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            return {"status": "sent", "action": "breathing_exercise_started"}
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar exercício de respiração: {e}")
            return {"status": "error", "message": str(e)}
    
    def notify_admin(self, message: str) -> Dict:
        """Enviar notificação para o administrador"""
        if not self.admin_chat_id:
            self.logger.warning("Admin chat ID não configurado")
            return {"status": "error", "message": "Admin not configured"}
        
        admin_ids = [id.strip() for id in self.admin_chat_id.split(',')]
        
        results = []
        for admin_id in admin_ids:
            result = self.telegram_service.send_text_message(admin_id, message)
            results.append(result)
        
        return {"status": "sent", "results": results}

