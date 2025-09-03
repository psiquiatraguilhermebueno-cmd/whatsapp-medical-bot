from typing import Dict, Optional
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.response import Response
from src.models.scale import Scale
from src.models.medication import Medication, MedicationConfirmation
from src.models.mood_chart import MoodChart, BreathingExercise, BreathingSession
from src.models.user import db
from src.services.whatsapp_service import WhatsAppService
from src.services.questionnaire_service import QuestionnaireService
from src.services.medication_service import MedicationService
from src.services.mood_service import MoodService
from src.services.admin_service import AdminService
from datetime import datetime, date
import re

class MessageHandler:
    """Handler principal para processar mensagens recebidas do WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.questionnaire_service = QuestionnaireService()
        self.medication_service = MedicationService()
        self.mood_service = MoodService()
        self.admin_service = AdminService()
        
        # Estados de conversa dos usuários
        self.user_states = {}
    
    def handle_message(self, message_data: Dict) -> Dict:
        """Processar mensagem recebida"""
        try:
            phone_number = message_data['from']
            message_text = message_data.get('text', '').strip()
            message_type = message_data.get('type')
            contact_name = message_data.get('contact_name', 'Usuário')
            
            # Verificar se é um comando administrativo
            if message_text.startswith('/'):
                return self.admin_service.handle_admin_command(phone_number, message_text, contact_name)
            
            # Verificar se é uma resposta administrativa
            admin_state = self.admin_service.admin_states.get(phone_number)
            if admin_state and admin_state.get('conversation_type'):
                return self.admin_service.handle_admin_response(phone_number, message_text, message_data)
            
            # Buscar paciente pelo número de telefone
            patient = Patient.query.filter_by(phone_number=phone_number).first()
            
            if not patient:
                return self._handle_unknown_user(phone_number, contact_name)
            
            # Processar diferentes tipos de mensagem
            if message_type == 'text':
                return self._handle_text_message(patient, message_text, message_data)
            elif message_type == 'interactive':
                return self._handle_interactive_message(patient, message_data)
            elif message_type == 'audio':
                return self._handle_audio_message(patient, message_data)
            elif message_type == 'document':
                return self._handle_document_message(patient, message_data)
            elif message_type == 'image' or message_type == 'video':
                return self._handle_media_message(patient, message_data)
            
            return {'status': 'processed', 'action': 'unknown_message_type'}
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_unknown_user(self, phone_number: str, contact_name: str) -> Dict:
        """Lidar com usuário não cadastrado"""
        message = f"""Olá {contact_name}! 👋
# === KILL SWITCH u-ETG (antes de enviar "não cadastrado") ===
try:
    # 1) Tenta obter o response_id do clique
    resp = (locals().get("response_id") or "")
    if (not resp) and ("interactive_data" in locals()):
        _idata = (locals().get("interactive_data") or {})
        _br = _idata.get("button_reply") or {}
        _lr = _idata.get("list_reply") or {}
        resp = (_br.get("id") or _br.get("title") or _lr.get("id") or _lr.get("title") or "")
    if (not resp) and ("message_data" in locals()):
        _idata = ((locals().get("message_data") or {}).get("interactive") or {})
        _br = _idata.get("button_reply") or {}
        _lr = _idata.get("list_reply") or {}
        resp = (_br.get("id") or _br.get("title") or _lr.get("id") or _lr.get("title") or "")

    # 2) Normaliza horários soltos (1215 / 12h15 / 12:15) -> slot_*
    import re
    if re.fullmatch(r"\s*\d{3,4}\s*", resp or "") and ":" not in resp:
        _num = re.sub(r"\D+", "", resp or "")
        if len(_num) == 3:
            resp = "{:02d}:{}".format(int(_num[:-2]), _num[-2:])
        else:
            resp = "{}:{}".format(_num[:2], _num[2:])
    _m = re.search(r"(\d{1,2})[:hH]?(\d{2})", resp or "")
    if _m:
        _cand = "{:02d}:{}".format(int(_m.group(1)), _m.group(2))
        _slot_titles = {"07:30": "slot_0730", "12:15": "slot_1215", "19:00": "slot_1900"}
        resp = _slot_titles.get(_cand, resp)

    # 3) Se for um slot u-ETG, processa AGORA e sai
    if str(resp).startswith("slot_") or resp in {"slot_0730","slot_1215","slot_1900"}:
        # normaliza phone para dígitos
        _raw_pn = (locals().get("phone_number") or (locals().get("user_info") or {}).get("phone_number") or "")
        _pn = "".join(ch for ch in str(_raw_pn) if ch.isdigit())
        _name = ((locals().get("user_info") or {}).get("name") or "Paciente")

        try:
            from src.jobs.uetg_scheduler import process_button_click
            ok = None
            # tenta assinaturas diferentes do process_button_click
            try:
                ok = process_button_click(user_id=_pn, response_id=resp, request_id="uETG-guard")
            except TypeError:
                try:
                    ok = process_button_click(resp, _pn, _name)
                except TypeError:
                    ok = process_button_click(_pn, resp)
            if ok is None:
                ok = True

            _human = {"slot_0730":"07:30","slot_1215":"12:15","slot_1900":"19:00"}.get(resp, "horário escolhido")
            try:
                self.whatsapp_service.send_text_message(_pn, "⏰ Horário confirmado: {} ✅".format(_human))
            except Exception:
                pass
            # marca como processado e NÃO envia "não cadastrado"
            return {"status":"processed","action":"uetg_slot_confirmed"}
        except Exception:
            # Se algo falhar aqui, pelo menos não bloqueie o usuário
            return {"status":"processed","action":"uetg_slot_click_seen"}
except Exception:
    # falha silenciosa -> cai no fluxo original apenas se NÃO for slot
    pass
# === FIM KILL SWITCH u-ETG ===

Você não está cadastrado no sistema de lembretes médicos.

Para ser cadastrado, entre em contato com seu profissional de saúde.

Se você é um profissional de saúde, use os comandos administrativos para gerenciar o sistema."""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        return {'status': 'processed', 'action': 'unknown_user_notified'}
    
    def _handle_text_message(self, patient: Patient, message_text: str, message_data: Dict) -> Dict:
        """Processar mensagem de texto"""
        phone_number = patient.phone_number
        message_lower = message_text.lower()
        
        # Verificar se o usuário está em uma conversa ativa
        user_state = self.user_states.get(phone_number, {})
        
        if user_state.get('active_conversation'):
            return self._handle_conversation_response(patient, message_text, user_state)
        
        # Mensagens gerais
        if any(greeting in message_lower for greeting in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite']):
            return self._send_welcome_message(patient)
        elif 'ajuda' in message_lower or 'help' in message_lower:
            return self._send_help_message(patient)
        elif 'medicação' in message_lower or 'medicamento' in message_lower:
            return self._handle_medication_query(patient)
        elif 'humor' in message_lower or 'afetivograma' in message_lower:
            return self._handle_mood_query(patient)
        elif 'respiração' in message_lower or 'respirar' in message_lower:
            return self._handle_breathing_query(patient)
        else:
            return self._send_default_response(patient)
    
    def _handle_interactive_message(self, patient: Patient, message_data: Dict) -> Dict:
        """Processar mensagem interativa (botões/listas)"""
        interactive_data = message_data.get('interactive', {})
        phone_number = patient.phone_number if patient else message_data['from']
        
        if interactive_data.get('type') == 'button_reply':
            button_id = interactive_data.get('button_reply', {}).get('id')
            
            # Verificar se é um botão administrativo
            if any(button_id.startswith(prefix) for prefix in ['patients_', 'reminders_', 'reports_', 'system_', 'back_main']):
                return self.admin_service.handle_admin_button(phone_number, button_id)
            
            # Botões de paciente
            if patient:
                return self._handle_button_response(patient, button_id)
            
        elif interactive_data.get('type') == 'list_reply':
            list_id = interactive_data.get('list_reply', {}).get('id')
            if patient:
                return self._handle_list_response(patient, list_id)
        
        return {'status': 'processed', 'action': 'interactive_message_processed'}
    
    def _handle_conversation_response(self, patient: Patient, message_text: str, user_state: Dict) -> Dict:
        """Processar resposta em conversa ativa"""
        conversation_type = user_state.get('conversation_type')
        
        if conversation_type == 'questionnaire':
            return self.questionnaire_service.process_questionnaire_response(patient, message_text, user_state)
        elif conversation_type == 'mood_chart':
            return self.mood_service.process_mood_response(patient, message_text, user_state)
        elif conversation_type == 'medication_confirmation':
            return self.medication_service.process_medication_confirmation(patient, message_text, user_state)
        
        return {'status': 'processed', 'action': 'conversation_response_processed'}
    
    def _handle_button_response(self, patient: Patient, button_id: str) -> Dict:
        """Processar resposta de botão"""
        if button_id.startswith('breathing_'):
            exercise_id = int(button_id.replace('breathing_', ''))
            return self._start_breathing_exercise(patient, exercise_id)
        elif button_id.startswith('medication_'):
            return self.medication_service.handle_medication_button(patient, button_id)
        elif button_id.startswith('mood_'):
            return self.mood_service.handle_mood_button(patient, button_id)
        elif button_id.startswith('start_scale_'):
            scale_type = button_id.replace('start_scale_', '')
            return self.questionnaire_service.start_questionnaire(patient, scale_type)
        elif button_id == 'start_mood_chart':
            return self.mood_service.start_mood_registration(patient)
        
        return {'status': 'processed', 'action': 'button_response_processed'}
    
    def _send_welcome_message(self, patient: Patient) -> Dict:
        """Enviar mensagem de boas-vindas"""
        message = f"""Olá {patient.name}! 👋

Bem-vindo ao seu assistente de saúde mental! 

Estou aqui para ajudar com:
🔹 Lembretes de medicação
🔹 Questionários de acompanhamento
🔹 Exercícios de respiração
🔹 Registro de humor

Digite "ajuda" para ver todas as opções disponíveis."""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        return {'status': 'processed', 'action': 'welcome_sent'}
    
    def _send_help_message(self, patient: Patient) -> Dict:
        """Enviar mensagem de ajuda"""
        message = """🆘 *Como posso ajudar você:*

📋 *Questionários:*
• Responda quando receber lembretes
• Digite "questionário" para ver pendentes

💊 *Medicação:*
• Confirme quando tomar seus remédios
• Digite "medicação" para ver horários

😊 *Humor:*
• Registre seu humor diário
• Digite "humor" para registrar agora

🫁 *Respiração:*
• Acesse exercícios de respiração
• Digite "respiração" para começar

❓ Digite "ajuda" a qualquer momento para ver esta mensagem novamente."""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        return {'status': 'processed', 'action': 'help_sent'}
    
    def _send_default_response(self, patient: Patient) -> Dict:
        """Enviar resposta padrão"""
        message = """Não entendi sua mensagem. 🤔

Digite "ajuda" para ver o que posso fazer por você, ou aguarde seus lembretes programados.

Se precisar de ajuda urgente, entre em contato com seu profissional de saúde."""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        return {'status': 'processed', 'action': 'default_response_sent'}
    
    def _handle_medication_query(self, patient: Patient) -> Dict:
        """Lidar com consultas sobre medicação"""
        return self.medication_service.send_medication_status(patient)
    
    def _handle_mood_query(self, patient: Patient) -> Dict:
        """Lidar com consultas sobre humor"""
        return self.mood_service.start_mood_registration(patient)
    
    def _handle_breathing_query(self, patient: Patient) -> Dict:
        """Lidar com consultas sobre exercícios de respiração"""
        exercises = BreathingExercise.query.filter_by(is_active=True).all()
        
        if not exercises:
            message = "Desculpe, não há exercícios de respiração disponíveis no momento."
            self.whatsapp_service.send_text_message(patient.phone_number, message)
            return {'status': 'processed', 'action': 'no_breathing_exercises'}
        
        # Criar lista de exercícios
        sections = [{
            "title": "Exercícios Disponíveis",
            "rows": [
                {
                    "id": f"breathing_{exercise.id}",
                    "title": exercise.name,
                    "description": f"{exercise.duration_minutes} min - {exercise.category}"
                }
                for exercise in exercises[:10]  # Limite de 10 exercícios
            ]
        }]
        
        self.whatsapp_service.send_list_message(
            patient.phone_number,
            "🫁 Exercícios de Respiração",
            "Escolha um exercício para começar:",
            "Ver exercícios",
            sections
        )
        
        return {'status': 'processed', 'action': 'breathing_exercises_sent'}
    
    def _handle_button_response(self, patient: Patient, button_id: str) -> Dict:
        """Processar resposta de botão"""
        if button_id.startswith('breathing_'):
            exercise_id = int(button_id.replace('breathing_', ''))
            return self._start_breathing_exercise(patient, exercise_id)
        elif button_id.startswith('medication_'):
            return self.medication_service.handle_medication_button(patient, button_id)
        elif button_id.startswith('mood_'):
            return self.mood_service.handle_mood_button(patient, button_id)
        
        return {'status': 'processed', 'action': 'button_response_processed'}
    
    def _start_breathing_exercise(self, patient: Patient, exercise_id: int) -> Dict:
        """Iniciar exercício de respiração"""
        exercise = BreathingExercise.query.get(exercise_id)
        if not exercise:
            message = "Exercício não encontrado."
            self.whatsapp_service.send_text_message(patient.phone_number, message)
            return {'status': 'error', 'action': 'exercise_not_found'}
        
        # Criar sessão de exercício
        session = BreathingSession(
            patient_id=patient.id,
            exercise_id=exercise.id,
            start_time=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # Enviar instruções
        instructions_text = f"""🫁 *{exercise.name}*

⏱️ Duração: {exercise.duration_minutes} minutos
📝 {exercise.description}

*Instruções:*
"""
        
        for i, instruction in enumerate(exercise.instructions, 1):
            instructions_text += f"{i}. {instruction}\n"
        
        instructions_text += "\n✨ Encontre um local tranquilo e comece quando estiver pronto!"
        
        self.whatsapp_service.send_text_message(patient.phone_number, instructions_text)
        
        # Se houver áudio, enviar também
        if exercise.audio_file_path:
            self.whatsapp_service.send_audio_message(patient.phone_number, exercise.audio_file_path)
        
        return {'status': 'processed', 'action': 'breathing_exercise_started'}
    
    def update_user_state(self, phone_number: str, state: Dict):
        """Atualizar estado do usuário"""
        self.user_states[phone_number] = state
    
    def clear_user_state(self, phone_number: str):
        """Limpar estado do usuário"""
        if phone_number in self.user_states:
            del self.user_states[phone_number]

