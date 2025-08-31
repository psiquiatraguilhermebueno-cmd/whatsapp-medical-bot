from typing import Dict, List, Optional
from src.models.patient import Patient
from src.models.scale import Scale
from src.models.response import Response
from src.models.user import db
from src.services.whatsapp_service import WhatsAppService
from datetime import datetime
import json

class QuestionnaireService:
    """Serviço para gerenciar questionários dinâmicos via WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
    
    def start_questionnaire(self, patient: Patient, scale_name: str) -> Dict:
        """Iniciar um questionário para o paciente"""
        scale = Scale.query.filter_by(name=scale_name).first()
        if not scale:
            return {'status': 'error', 'message': 'Escala não encontrada'}
        
        # Enviar mensagem de introdução
        intro_message = f"""📋 *{scale.title}*

{scale.description}

Vou fazer algumas perguntas sobre como você tem se sentido. Responda com sinceridade - suas respostas são confidenciais e ajudarão no seu acompanhamento.

Vamos começar? 🤝"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, intro_message)
        
        # Iniciar primeira pergunta
        return self._send_question(patient, scale, 0)
    
    def _send_question(self, patient: Patient, scale: Scale, question_index: int) -> Dict:
        """Enviar uma pergunta específica do questionário"""
        if question_index >= len(scale.questions):
            return self._finish_questionnaire(patient, scale)
        
        question = scale.questions[question_index]
        
        # Criar opções de resposta baseadas no tipo de escala
        if scale.name in ['PHQ-9', 'GAD-7']:
            # Escala 0-3
            buttons = [
                {'id': f'q_{question_index}_0', 'title': '0 - Nem um pouco'},
                {'id': f'q_{question_index}_1', 'title': '1 - Vários dias'},
                {'id': f'q_{question_index}_2', 'title': '2 - Mais da metade'},
                {'id': f'q_{question_index}_3', 'title': '3 - Quase todos os dias'}
            ]
        elif scale.name == 'MDQ':
            # Sim/Não
            buttons = [
                {'id': f'q_{question_index}_1', 'title': 'Sim'},
                {'id': f'q_{question_index}_0', 'title': 'Não'}
            ]
        elif scale.name == 'ASRS':
            # Escala 0-4
            buttons = [
                {'id': f'q_{question_index}_0', 'title': '0 - Nunca'},
                {'id': f'q_{question_index}_1', 'title': '1 - Raramente'},
                {'id': f'q_{question_index}_2', 'title': '2 - Às vezes'},
                {'id': f'q_{question_index}_3', 'title': '3 - Frequentemente'},
                {'id': f'q_{question_index}_4', 'title': '4 - Muito frequente'}
            ]
        elif scale.name in ['AUDIT', 'DAST-10']:
            # Varia por pergunta - usar resposta de texto
            return self._send_text_question(patient, scale, question_index)
        else:
            # Padrão: escala 0-3
            buttons = [
                {'id': f'q_{question_index}_0', 'title': '0 - Não'},
                {'id': f'q_{question_index}_1', 'title': '1 - Pouco'},
                {'id': f'q_{question_index}_2', 'title': '2 - Moderado'},
                {'id': f'q_{question_index}_3', 'title': '3 - Muito'}
            ]
        
        # Enviar pergunta com botões
        header = f"Pergunta {question_index + 1}/{len(scale.questions)}"
        body = f"*{question}*\n\nComo isso se aplica a você?"
        
        result = self.whatsapp_service.send_interactive_message(
            patient.phone_number, header, body, buttons
        )
        
        # Salvar estado da conversa
        self._save_conversation_state(patient, scale, question_index)
        
        return {'status': 'processed', 'action': 'question_sent', 'question_index': question_index}
    
    def _send_text_question(self, patient: Patient, scale: Scale, question_index: int) -> Dict:
        """Enviar pergunta que requer resposta de texto"""
        question = scale.questions[question_index]
        
        message = f"""📋 *Pergunta {question_index + 1}/{len(scale.questions)}*

{question}

Por favor, responda com um número ou texto conforme apropriado."""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        # Salvar estado da conversa
        self._save_conversation_state(patient, scale, question_index)
        
        return {'status': 'processed', 'action': 'text_question_sent', 'question_index': question_index}
    
    def process_questionnaire_response(self, patient: Patient, response_text: str, user_state: Dict) -> Dict:
        """Processar resposta do questionário"""
        scale_name = user_state.get('scale_name')
        question_index = user_state.get('question_index', 0)
        responses = user_state.get('responses', [])
        
        scale = Scale.query.filter_by(name=scale_name).first()
        if not scale:
            return {'status': 'error', 'message': 'Escala não encontrada'}
        
        # Processar resposta
        try:
            if response_text.startswith('q_'):
                # Resposta de botão
                parts = response_text.split('_')
                response_value = int(parts[2])
            else:
                # Resposta de texto
                response_value = self._parse_text_response(response_text, scale, question_index)
        except:
            # Resposta inválida
            message = "Resposta inválida. Por favor, use os botões ou digite um número válido."
            self.whatsapp_service.send_text_message(patient.phone_number, message)
            return {'status': 'error', 'action': 'invalid_response'}
        
        # Adicionar resposta à lista
        responses.append(response_value)
        
        # Verificar se há mais perguntas
        if question_index + 1 < len(scale.questions):
            # Próxima pergunta
            user_state['responses'] = responses
            user_state['question_index'] = question_index + 1
            return self._send_question(patient, scale, question_index + 1)
        else:
            # Finalizar questionário
            return self._finish_questionnaire(patient, scale, responses)
    
    def _parse_text_response(self, response_text: str, scale: Scale, question_index: int) -> int:
        """Converter resposta de texto em valor numérico"""
        # Tentar extrair número da resposta
        import re
        numbers = re.findall(r'\d+', response_text)
        if numbers:
            return int(numbers[0])
        
        # Mapear respostas textuais comuns
        response_lower = response_text.lower()
        
        if scale.name == 'MDQ':
            if any(word in response_lower for word in ['sim', 'yes', 's']):
                return 1
            else:
                return 0
        elif scale.name in ['DAST-10']:
            if any(word in response_lower for word in ['sim', 'yes', 's']):
                return 1
            else:
                return 0
        
        # Padrão: tentar converter diretamente
        try:
            return int(response_text)
        except:
            return 0
    
    def _finish_questionnaire(self, patient: Patient, scale: Scale, responses: List[int] = None) -> Dict:
        """Finalizar questionário e calcular pontuação"""
        if not responses:
            responses = []
        
        # Calcular pontuação total
        total_score = sum(responses)
        
        # Determinar categoria baseada nas regras de pontuação
        category = 'Não categorizado'
        is_alarming = total_score >= scale.alarm_threshold
        
        for rule in scale.scoring_rules:
            if rule['min_score'] <= total_score <= rule['max_score']:
                category = rule['category']
                break
        
        # Salvar resposta no banco de dados
        response_record = Response(
            patient_id=patient.id,
            reminder_id=None,  # Será preenchido se vier de um lembrete
            response_data={'responses': responses, 'scale_name': scale.name},
            score=total_score,
            is_alarming=is_alarming
        )
        db.session.add(response_record)
        db.session.commit()
        
        # Enviar resultado para o paciente
        result_message = f"""✅ *Questionário concluído!*

📊 *Resultado:*
• Pontuação: {total_score}/{len(scale.questions) * 3}
• Categoria: {category}

Obrigado por responder! Suas respostas foram enviadas para seu profissional de saúde."""
        
        if is_alarming:
            result_message += f"""

⚠️ *Importante:* Sua pontuação indica que você pode estar passando por um momento difícil. 

Recomendo que entre em contato com seu profissional de saúde o mais breve possível.

🆘 Se você está tendo pensamentos de autolesão, procure ajuda imediatamente:
• CVV: 188 (24h)
• SAMU: 192
• Emergência: 190"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, result_message)
        
        # Notificar profissional se pontuação for alarmante
        if is_alarming:
            self._notify_professional_alarm(patient, scale, total_score, category)
        
        # Limpar estado da conversa
        self._clear_conversation_state(patient)
        
        return {
            'status': 'completed',
            'action': 'questionnaire_finished',
            'score': total_score,
            'category': category,
            'is_alarming': is_alarming
        }
    
    def _notify_professional_alarm(self, patient: Patient, scale: Scale, score: int, category: str):
        """Notificar profissional sobre pontuação alarmante"""
        # Aqui você implementaria a lógica para notificar o profissional
        # Por exemplo, enviar mensagem para um número específico ou email
        
        alarm_message = f"""🚨 *ALERTA - Pontuação Elevada*

👤 *Paciente:* {patient.name}
📱 *Telefone:* {patient.phone_number}
📋 *Escala:* {scale.title}
📊 *Pontuação:* {score}
📈 *Categoria:* {category}
📅 *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

⚠️ Recomenda-se contato imediato com o paciente."""
        
        # Implementar envio para profissional
        # self.whatsapp_service.send_text_message(professional_number, alarm_message)
        
        print(f"ALERTA: {alarm_message}")  # Log temporário
    
    def _save_conversation_state(self, patient: Patient, scale: Scale, question_index: int):
        """Salvar estado da conversa"""
        # Implementar salvamento do estado
        # Por simplicidade, usando variável de classe
        pass
    
    def _clear_conversation_state(self, patient: Patient):
        """Limpar estado da conversa"""
        # Implementar limpeza do estado
        pass

