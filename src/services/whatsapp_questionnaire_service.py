import logging
import os
import json
from typing import Dict, List
from datetime import datetime
from src.services.whatsapp_service import WhatsAppService
from src.models.patient import Patient
from src.models.scale import Scale
from src.models.response import Response
from src.models.user import db

class WhatsAppQuestionnaireService:
    """Serviço para gerenciar questionários dinâmicos via WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.logger = logging.getLogger(__name__)
        
        # Estados de questionários ativos
        self.active_questionnaires = {}
    
    def start_questionnaire(self, phone_number: str, scale_name: str, patient: Patient) -> Dict:
        """Iniciar questionário para uma escala específica"""
        try:
            # Buscar escala no banco de dados
            scale = Scale.query.filter_by(name=scale_name).first()
            if not scale:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    f"❌ Escala '{scale_name}' não encontrada."
                )
                return {"status": "error", "message": "Scale not found"}
            
            # Verificar se já respondeu hoje
            today = datetime.now().date()
            existing_response = Response.query.filter(
                Response.patient_id == patient.id,
                Response.scale_id == scale.id,
                db.func.date(Response.created_at) == today
            ).first()
            
            if existing_response:
                message = f"""📋 *{scale.name}*

Você já respondeu este questionário hoje!

📊 *Sua pontuação:* {existing_response.total_score} pontos
🕐 *Respondido às:* {existing_response.created_at.strftime('%H:%M')}

Obrigado por manter seus registros em dia! 👏"""
                
                self.whatsapp_service.send_text_message(phone_number, message)
                return {"status": "already_completed", "action": "questionnaire_already_completed"}
            
            # Inicializar estado do questionário
            questions = json.loads(scale.questions)
            questionnaire_state = {
                "patient_id": patient.id,
                "scale_id": scale.id,
                "scale_name": scale.name,
                "questions": questions,
                "current_question": 0,
                "responses": [],
                "started_at": datetime.now().isoformat()
            }
            
            self.active_questionnaires[phone_number] = questionnaire_state
            
            # Enviar primeira pergunta
            return self._send_current_question(phone_number)
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar questionário: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_response(self, phone_number: str, callback_data: str, patient: Patient) -> Dict:
        """Processar resposta de questionário"""
        try:
            if phone_number not in self.active_questionnaires:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "❌ Nenhum questionário ativo encontrado. Use o comando para iniciar um novo questionário."
                )
                return {"status": "error", "message": "No active questionnaire"}
            
            state = self.active_questionnaires[phone_number]
            
            # Extrair resposta do callback_data
            if not callback_data.startswith('questionnaire_answer_'):
                return {"status": "error", "message": "Invalid callback format"}
            
            answer_value = int(callback_data.split('_')[-1])
            
            # Registrar resposta
            state["responses"].append(answer_value)
            
            # Avançar para próxima pergunta
            state["current_question"] += 1
            
            # Verificar se terminou o questionário
            if state["current_question"] >= len(state["questions"]):
                return self._finish_questionnaire(phone_number, state)
            else:
                return self._send_current_question(phone_number)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar resposta: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_current_question(self, phone_number: str) -> Dict:
        """Enviar pergunta atual do questionário"""
        try:
            state = self.active_questionnaires[phone_number]
            current_q = state["current_question"]
            questions = state["questions"]
            
            if current_q >= len(questions):
                return {"status": "error", "message": "No more questions"}
            
            question_data = questions[current_q]
            question_text = question_data["question"]
            options = question_data["options"]
            
            # Cabeçalho com progresso
            progress = f"({current_q + 1}/{len(questions)})"
            header = f"📋 {state['scale_name']} {progress}"
            
            # Corpo da mensagem
            body = f"*Pergunta {current_q + 1}:*\n\n{question_text}"
            
            # Preparar botões (máximo 3 para WhatsApp)
            buttons = []
            for i, option in enumerate(options[:3]):
                buttons.append({
                    "id": f"questionnaire_answer_{option['value']}",
                    "title": f"{option['value']}. {option['text'][:15]}..."  # Limitar texto do botão
                })
            
            # Se há mais de 3 opções, usar lista
            if len(options) > 3:
                sections = [{
                    "title": "Opções de Resposta",
                    "rows": [
                        {
                            "id": f"questionnaire_answer_{option['value']}",
                            "title": f"{option['value']}. {option['text'][:20]}",
                            "description": option['text'][:60] if len(option['text']) > 20 else ""
                        }
                        for option in options
                    ]
                }]
                
                self.whatsapp_service.send_list_message(
                    phone_number,
                    header,
                    body,
                    "Escolher Resposta",
                    sections
                )
            else:
                self.whatsapp_service.send_interactive_message(
                    phone_number,
                    header,
                    body,
                    buttons
                )
            
            return {"status": "sent", "action": "question_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar pergunta: {e}")
            return {"status": "error", "message": str(e)}
    
    def _finish_questionnaire(self, phone_number: str, state: Dict) -> Dict:
        """Finalizar questionário e calcular pontuação"""
        try:
            # Calcular pontuação total
            total_score = sum(state["responses"])
            
            # Buscar escala para obter thresholds
            scale = Scale.query.get(state["scale_id"])
            if not scale:
                return {"status": "error", "message": "Scale not found"}
            
            # Determinar se é um alerta
            thresholds = json.loads(scale.scoring_thresholds) if scale.scoring_thresholds else {}
            alert_threshold = thresholds.get("alert", 999)
            is_alert = total_score >= alert_threshold
            
            # Salvar resposta no banco de dados
            response = Response(
                patient_id=state["patient_id"],
                scale_id=state["scale_id"],
                responses=json.dumps(state["responses"]),
                total_score=total_score,
                alert_triggered=is_alert,
                created_at=datetime.now()
            )
            
            db.session.add(response)
            db.session.commit()
            
            # Enviar resultado para o paciente
            self._send_questionnaire_result(phone_number, state, total_score, is_alert, scale)
            
            # Notificar administrador se necessário
            if is_alert:
                self._notify_admin_alert(state, total_score, scale)
            
            # Limpar estado
            del self.active_questionnaires[phone_number]
            
            return {
                "status": "completed",
                "action": "questionnaire_finished",
                "score": total_score,
                "alert": is_alert,
                "response_id": response.id
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao finalizar questionário: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_questionnaire_result(self, phone_number: str, state: Dict, score: int, is_alert: bool, scale: Scale) -> None:
        """Enviar resultado do questionário para o paciente"""
        try:
            scale_name = state["scale_name"]
            
            # Determinar emoji e mensagem baseado na pontuação
            if is_alert:
                emoji = "🚨"
                status_msg = "Pontuação elevada - Recomendamos contato com seu profissional de saúde"
            elif score <= (json.loads(scale.scoring_thresholds).get("low", 0) if scale.scoring_thresholds else 5):
                emoji = "✅"
                status_msg = "Pontuação baixa - Continue cuidando bem de você!"
            else:
                emoji = "⚠️"
                status_msg = "Pontuação moderada - Mantenha o acompanhamento"
            
            message = f"""✅ *Questionário Concluído*

📋 *{scale_name}*
📊 *Sua pontuação:* {score} pontos
{emoji} *Status:* {status_msg}
📅 *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

Obrigado por responder! Suas informações foram enviadas ao seu profissional de saúde.

"""
            
            if is_alert:
                message += """💙 *Lembre-se:* Você não está sozinho. Se precisar de apoio imediato, entre em contato com seu profissional de saúde.

🆘 *Emergência:* CVV 188 (24h)"""
            else:
                message += "Continue mantendo seus registros em dia! 💚"
            
            self.whatsapp_service.send_text_message(phone_number, message)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar resultado: {e}")
    
    def _notify_admin_alert(self, state: Dict, score: int, scale: Scale) -> None:
        """Notificar administrador sobre pontuação de alerta"""
        try:
            patient = Patient.query.get(state["patient_id"])
            if not patient:
                return
            
            admin_phone = os.getenv('ADMIN_PHONE_NUMBER')
            if not admin_phone:
                return
            
            message = f"""🚨 *ALERTA - Pontuação Elevada*

👤 *Paciente:* {patient.name}
📋 *Escala:* {scale.name}
📊 *Pontuação:* {score} pontos
📅 *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

💡 *Recomendação:* Considere entrar em contato com o paciente para avaliação.

📱 *Contato:* {patient.whatsapp_phone}"""
            
            # Enviar para todos os admins
            admin_phones = [phone.strip() for phone in admin_phone.split(',')]
            for admin in admin_phones:
                self.whatsapp_service.send_text_message(admin, message)
                
        except Exception as e:
            self.logger.error(f"Erro ao notificar admin: {e}")
    
    def cancel_questionnaire(self, phone_number: str) -> Dict:
        """Cancelar questionário ativo"""
        if phone_number in self.active_questionnaires:
            del self.active_questionnaires[phone_number]
            
            self.whatsapp_service.send_text_message(
                phone_number,
                "❌ Questionário cancelado. Você pode iniciar um novo a qualquer momento."
            )
            
            return {"status": "cancelled", "action": "questionnaire_cancelled"}
        
        return {"status": "error", "message": "No active questionnaire"}
    
    def get_available_scales(self) -> List[Dict]:
        """Obter escalas disponíveis"""
        scales = Scale.query.filter_by(is_active=True).all()
        return [
            {
                "name": scale.name,
                "description": scale.description,
                "questions_count": len(json.loads(scale.questions)) if scale.questions else 0
            }
            for scale in scales
        ]
    
    def send_scale_menu(self, phone_number: str, patient: Patient) -> Dict:
        """Enviar menu de escalas disponíveis"""
        try:
            scales = self.get_available_scales()
            
            if not scales:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "❌ Nenhuma escala disponível no momento."
                )
                return {"status": "error", "message": "No scales available"}
            
            message = """📋 *Questionários Disponíveis*

Escolha um questionário para responder:"""
            
            # Preparar seções para lista
            sections = [{
                "title": "Escalas Clínicas",
                "rows": [
                    {
                        "id": f"start_questionnaire_{scale['name']}",
                        "title": scale['name'],
                        "description": f"{scale['questions_count']} perguntas - {scale['description'][:50]}..."
                    }
                    for scale in scales[:10]  # Máximo 10 escalas
                ]
            }]
            
            self.whatsapp_service.send_list_message(
                phone_number,
                "Questionários",
                message,
                "Escolher Questionário",
                sections
            )
            
            return {"status": "sent", "action": "scales_menu_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar menu de escalas: {e}")
            return {"status": "error", "message": str(e)}

