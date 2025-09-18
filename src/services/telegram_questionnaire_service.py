import logging
import os
from typing import Dict, List, Any
from src.services.telegram_service import TelegramService
from src.models.patient import Patient
from src.models.scale import Scale
from src.models.response import Response
from src.models.user import db
from datetime import datetime

class TelegramQuestionnaireService:
    """Serviço para gerenciar questionários dinâmicos via Telegram"""
    
    def __init__(self):
        self.telegram_service = TelegramService(bot_token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.logger = logging.getLogger(__name__)
        
        # Estados de questionários ativos
        self.active_questionnaires = {}
    
    def start_questionnaire(self, chat_id: str, scale_name: str, patient: Patient) -> Dict:
        """
        Iniciar um questionário para um paciente
        
        Args:
            chat_id: ID do chat do Telegram
            scale_name: Nome da escala (PHQ-9, GAD-7, etc.)
            patient: Objeto Patient
            
        Returns:
            Resultado da operação
        """
        try:
            # Buscar escala
            scale = Scale.query.filter_by(name=scale_name).first()
            if not scale:
                self.telegram_service.send_text_message(
                    chat_id,
                    f"❌ Escala '{scale_name}' não encontrada."
                )
                return {"status": "error", "message": "Scale not found"}
            
            # Parsear perguntas da escala
            scale_data = scale.questions_data or {}
            questions = scale_data.get('questions', [])
            
            if not questions:
                self.telegram_service.send_text_message(
                    chat_id,
                    f"❌ Escala '{scale_name}' não possui perguntas configuradas."
                )
                return {"status": "error", "message": "No questions found"}
            
            # Inicializar estado do questionário
            questionnaire_state = {
                "scale_id": scale.id,
                "scale_name": scale_name,
                "patient_id": patient.id,
                "questions": questions,
                "current_question": 0,
                "responses": [],
                "started_at": datetime.now().isoformat()
            }
            
            self.active_questionnaires[chat_id] = questionnaire_state
            
            # Enviar primeira pergunta
            return self._send_current_question(chat_id)
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar questionário: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_response(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """
        Processar resposta de questionário
        
        Args:
            chat_id: ID do chat
            callback_data: Dados do callback (ex: questionnaire_answer_1)
            patient: Objeto Patient
            
        Returns:
            Resultado do processamento
        """
        try:
            if chat_id not in self.active_questionnaires:
                self.telegram_service.send_text_message(
                    chat_id,
                    "❌ Nenhum questionário ativo encontrado."
                )
                return {"status": "error", "message": "No active questionnaire"}
            
            state = self.active_questionnaires[chat_id]
            
            # Extrair resposta do callback_data
            # Formato: questionnaire_answer_X onde X é o índice da resposta
            if not callback_data.startswith('questionnaire_answer_'):
                return {"status": "error", "message": "Invalid callback format"}
            
            answer_index = int(callback_data.split('_')[-1])
            current_question_index = state["current_question"]
            questions = state["questions"]
            
            if current_question_index >= len(questions):
                return {"status": "error", "message": "Invalid question index"}
            
            current_question = questions[current_question_index]
            options = current_question.get('options', [])
            
            if answer_index >= len(options):
                return {"status": "error", "message": "Invalid answer index"}
            
            selected_option = options[answer_index]
            
            # Salvar resposta
            response_data = {
                "question": current_question.get('text', ''),
                "answer": selected_option.get('text', ''),
                "score": selected_option.get('score', 0)
            }
            
            state["responses"].append(response_data)
            
            # Avançar para próxima pergunta
            state["current_question"] += 1
            
            # Verificar se terminou o questionário
            if state["current_question"] >= len(questions):
                return self._finish_questionnaire(chat_id, state)
            else:
                return self._send_current_question(chat_id)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar resposta: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_current_question(self, chat_id: str) -> Dict:
        """Enviar pergunta atual do questionário"""
        try:
            state = self.active_questionnaires[chat_id]
            questions = state["questions"]
            current_index = state["current_question"]
            
            if current_index >= len(questions):
                return {"status": "error", "message": "No more questions"}
            
            current_question = questions[current_index]
            question_text = current_question.get('text', '')
            options = current_question.get('options', [])
            
            # Montar mensagem
            progress = f"({current_index + 1}/{len(questions)})"
            message = f"📋 *{state['scale_name']}* {progress}\n\n{question_text}"
            
            # Montar botões
            buttons = []
            for i, option in enumerate(options):
                buttons.append({
                    "text": option.get('text', f'Opção {i+1}'),
                    "callback_data": f"questionnaire_answer_{i}"
                })
            
            self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            return {"status": "sent", "action": "question_sent", "question_index": current_index}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar pergunta: {e}")
            return {"status": "error", "message": str(e)}
    
    def _finish_questionnaire(self, chat_id: str, state: Dict) -> Dict:
        """Finalizar questionário e calcular pontuação"""
        try:
            # Calcular pontuação total
            total_score = sum(response.get('score', 0) for response in state['responses'])
            
            # Buscar escala para obter categorias
            scale = Scale.query.get(state['scale_id'])
            if not scale:
                return {"status": "error", "message": "Scale not found"}
            
            scale_data = scale.questions_data or {}
            scoring = scale_data.get('scoring', {})
            categories = scoring.get('categories', [])
            
            # Determinar categoria baseada na pontuação
            category = "Não categorizado"
            is_alarming = False
            
            for cat in categories:
                min_score = cat.get('min_score', 0)
                max_score = cat.get('max_score', 999)
                
                if min_score <= total_score <= max_score:
                    category = cat.get('name', 'Não categorizado')
                    is_alarming = cat.get('alarming', False)
                    break
            
            # Salvar resposta no banco de dados
            response = Response(
                patient_id=state['patient_id'],
                reminder_id=None,  # Pode ser None se foi iniciado manualmente
                response_data={
                    'scale_name': state['scale_name'],
                    'responses': state['responses'],
                    'total_questions': len(state['questions'])
                },
                score=total_score,
                category=category,
                is_alarming=is_alarming
            )
            
            db.session.add(response)
            db.session.commit()
            
            # Enviar resultado para o paciente
            self._send_questionnaire_result(chat_id, state['scale_name'], total_score, category, is_alarming)
            
            # Notificar administrador se for alarmante
            if is_alarming:
                self._notify_admin_alarming_result(state, total_score, category)
            
            # Limpar estado
            del self.active_questionnaires[chat_id]
            
            return {
                "status": "completed",
                "action": "questionnaire_finished",
                "score": total_score,
                "category": category,
                "is_alarming": is_alarming,
                "response_id": response.id
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao finalizar questionário: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_questionnaire_result(self, chat_id: str, scale_name: str, score: int, category: str, is_alarming: bool) -> None:
        """Enviar resultado do questionário para o paciente"""
        
        if is_alarming:
            message = f"""✅ *Questionário {scale_name} Concluído*

📊 *Sua pontuação:* {score}
📋 *Categoria:* {category}

🤗 Obrigado por responder ao questionário. Suas respostas foram enviadas ao seu profissional de saúde.

💙 *Lembre-se:* Você não está sozinho. Se estiver passando por um momento difícil, entre em contato com seu profissional de saúde.

🆘 *Em caso de emergência:* CVV 188 (24h)"""
        else:
            message = f"""✅ *Questionário {scale_name} Concluído*

📊 *Sua pontuação:* {score}
📋 *Categoria:* {category}

🤗 Obrigado por responder ao questionário. Suas respostas foram enviadas ao seu profissional de saúde.

Continue cuidando bem de você! 💚"""
        
        self.telegram_service.send_text_message(chat_id, message)
    
    def _notify_admin_alarming_result(self, state: Dict, score: int, category: str) -> None:
        """Notificar administrador sobre resultado alarmante"""
        try:
            patient = Patient.query.get(state['patient_id'])
            if not patient:
                return
            
            admin_chat_id = os.getenv('ADMIN_CHAT_ID')
            if not admin_chat_id:
                return
            
            message = f"""🚨 *ALERTA - Pontuação Preocupante*

👤 *Paciente:* {patient.name}
📋 *Escala:* {state['scale_name']}
📊 *Pontuação:* {score}
📈 *Categoria:* {category}
📅 *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

⚠️ *Ação recomendada:* Entre em contato com o paciente para avaliação."""
            
            # Enviar para todos os admins
            admin_ids = [id.strip() for id in admin_chat_id.split(',')]
            for admin_id in admin_ids:
                self.telegram_service.send_text_message(admin_id, message)
                
        except Exception as e:
            self.logger.error(f"Erro ao notificar admin: {e}")
    
    def cancel_questionnaire(self, chat_id: str) -> Dict:
        """Cancelar questionário ativo"""
        if chat_id in self.active_questionnaires:
            del self.active_questionnaires[chat_id]
            
            self.telegram_service.send_text_message(
                chat_id,
                "❌ Questionário cancelado."
            )
            
            return {"status": "cancelled", "action": "questionnaire_cancelled"}
        
        return {"status": "error", "message": "No active questionnaire"}
    
    def get_available_scales(self) -> List[Dict]:
        """Obter lista de escalas disponíveis"""
        scales = Scale.query.filter_by(is_active=True).all()
        
        return [
            {
                "id": scale.id,
                "name": scale.name,
                "description": scale.description,
                "question_count": len(scale.questions_data.get('questions', []) if scale.questions_data else [])
            }
            for scale in scales
        ]
    
    def send_scale_selection_menu(self, chat_id: str, patient: Patient) -> Dict:
        """Enviar menu de seleção de escalas"""
        try:
            scales = self.get_available_scales()
            
            if not scales:
                self.telegram_service.send_text_message(
                    chat_id,
                    "❌ Nenhuma escala disponível no momento."
                )
                return {"status": "error", "message": "No scales available"}
            
            message = """📋 *Questionários Disponíveis*

Escolha um questionário para responder:"""
            
            buttons = []
            for scale in scales:
                buttons.append({
                    "text": f"{scale['name']} ({scale['question_count']} perguntas)",
                    "callback_data": f"start_questionnaire_{scale['name']}"
                })
            
            self.telegram_service.send_interactive_message(chat_id, message, buttons)
            
            return {"status": "sent", "action": "scale_menu_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar menu de escalas: {e}")
            return {"status": "error", "message": str(e)}

