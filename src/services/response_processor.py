"""
Processador de respostas automáticas para questionários médicos
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.templates.whatsapp_templates import *

logger = logging.getLogger(__name__)

class QuestionnaireSession:
    """Gerencia sessão de questionário ativo"""
    
    def __init__(self, patient_id: int, questionnaire_type: str, phone: str):
        self.patient_id = patient_id
        self.questionnaire_type = questionnaire_type
        self.phone = phone
        self.current_question = 0
        self.responses = []
        self.started_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=2)
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def add_response(self, response: str) -> bool:
        """Adiciona resposta e retorna se é válida"""
        try:
            # Converte resposta para pontuação
            score_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4}
            if response.lower() in score_map:
                self.responses.append(score_map[response.lower()])
                self.current_question += 1
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao processar resposta: {e}")
            return False
    
    def get_total_score(self) -> int:
        return sum(self.responses)
    
    def is_complete(self) -> bool:
        """Verifica se questionário está completo"""
        question_counts = {
            'uetg': 3,
            'gad7': 7, 
            'phq9': 9,
            'asrs18': 18
        }
        return len(self.responses) >= question_counts.get(self.questionnaire_type, 0)

class ResponseProcessor:
    """Processa respostas automáticas do WhatsApp"""
    
    def __init__(self):
        self.active_sessions: Dict[str, QuestionnaireSession] = {}
        self.score_ranges = calculate_scores()
    
    def start_questionnaire(self, patient_id: int, phone: str, questionnaire_type: str) -> str:
        """Inicia novo questionário"""
        try:
            # Remove sessão anterior se existir
            if phone in self.active_sessions:
                del self.active_sessions[phone]
            
            # Cria nova sessão
            session = QuestionnaireSession(patient_id, questionnaire_type, phone)
            self.active_sessions[phone] = session
            
            # Retorna primeira pergunta
            templates = {
                'uetg': UETG_TEMPLATES,
                'gad7': GAD7_TEMPLATES,
                'phq9': PHQ9_TEMPLATES,
                'asrs18': ASRS18_TEMPLATES
            }
            
            template = templates[questionnaire_type]['start']['template']
            logger.info(f"Questionário {questionnaire_type} iniciado para paciente {patient_id}")
            
            return template
            
        except Exception as e:
            logger.error(f"Erro ao iniciar questionário: {e}")
            return "❌ Erro ao iniciar questionário. Tente novamente."
    
    def process_response(self, phone: str, message: str) -> Optional[str]:
        """Processa resposta do usuário"""
        try:
            # Verifica se há sessão ativa
            if phone not in self.active_sessions:
                return self._handle_no_session(message)
            
            session = self.active_sessions[phone]
            
            # Verifica se sessão expirou
            if session.is_expired():
                del self.active_sessions[phone]
                return WELCOME_MESSAGES['session_timeout']
            
            # Processa comandos especiais
            if message.lower() in ['ajuda', 'help']:
                return WELCOME_MESSAGES['help']
            elif message.lower() == 'status':
                return self._get_status_message(session)
            
            # Processa resposta do questionário
            if not session.add_response(message):
                return WELCOME_MESSAGES['invalid_response']
            
            # Verifica se questionário está completo
            if session.is_complete():
                result = self._generate_result(session)
                del self.active_sessions[phone]
                return result
            
            # Retorna próxima pergunta
            return self._get_next_question(session)
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta: {e}")
            return "❌ Erro interno. Tente novamente."
    
    def _handle_no_session(self, message: str) -> str:
        """Trata mensagens sem sessão ativa"""
        if message.lower() in ['ajuda', 'help']:
            return WELCOME_MESSAGES['help']
        elif message.lower() == 'oi' or message.lower() == 'olá':
            return WELCOME_MESSAGES['first_contact']
        else:
            return "Não há questionário ativo. Digite *ajuda* para mais informações."
    
    def _get_next_question(self, session: QuestionnaireSession) -> str:
        """Retorna próxima pergunta do questionário"""
        try:
            question_num = session.current_question + 1
            
            if session.questionnaire_type == 'uetg':
                if question_num == 2:
                    return UETG_TEMPLATES['question_2']['template']
                elif question_num == 3:
                    return UETG_TEMPLATES['question_3']['template']
            
            elif session.questionnaire_type in ['gad7', 'phq9']:
                templates = GAD7_TEMPLATES if session.questionnaire_type == 'gad7' else PHQ9_TEMPLATES
                questions = templates['questions']
                
                if question_num <= len(questions):
                    return f"*{question_num + 1}.* {questions[question_num - 1]}\n\na) Nenhuma vez (0)\nb) Vários dias (1)\nc) Mais da metade dos dias (2)\nd) Quase todos os dias (3)\n\nResponda apenas com a letra (a, b, c ou d)"
            
            elif session.questionnaire_type == 'asrs18':
                questions = ASRS18_TEMPLATES['questions']
                
                if question_num <= len(questions):
                    return f"*{question_num + 1}.* {questions[question_num - 1]}\n\na) Nunca (0)\nb) Raramente (1)\nc) Às vezes (2)\nd) Frequentemente (3)\ne) Muito frequentemente (4)\n\nResponda apenas com a letra (a, b, c, d ou e)"
            
            return "Erro ao carregar próxima pergunta."
            
        except Exception as e:
            logger.error(f"Erro ao gerar próxima pergunta: {e}")
            return "❌ Erro ao carregar pergunta."
    
    def _generate_result(self, session: QuestionnaireSession) -> str:
        """Gera resultado final do questionário"""
        try:
            score = session.get_total_score()
            questionnaire_type = session.questionnaire_type
            ranges = self.score_ranges[questionnaire_type]
            
            # Determina categoria do resultado
            result_category = None
            for category, (min_score, max_score) in ranges.items():
                if min_score <= score <= max_score:
                    result_category = category
                    break
            
            if not result_category:
                return "❌ Erro ao calcular resultado."
            
            # Seleciona template de resultado
            templates = {
                'uetg': UETG_TEMPLATES,
                'gad7': GAD7_TEMPLATES,
                'phq9': PHQ9_TEMPLATES,
                'asrs18': ASRS18_TEMPLATES
            }
            
            template_key = f"result_{result_category}"
            template = templates[questionnaire_type][template_key]['template']
            
            # Calcula próximo teste (exemplo: 1 semana)
            next_test = (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y")
            
            # Formata resultado
            result = template.format(score=score, next_test=next_test)
            
            # Salva resultado no banco (implementar depois)
            self._save_result(session, score, result_category)
            
            logger.info(f"Questionário {questionnaire_type} concluído - Paciente {session.patient_id} - Score: {score}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar resultado: {e}")
            return "❌ Erro ao calcular resultado."
    
    def _save_result(self, session: QuestionnaireSession, score: int, category: str):
        """Salva resultado no banco de dados"""
        try:
            # TODO: Implementar salvamento no banco
            # Por enquanto apenas log
            logger.info(f"Resultado salvo - Paciente: {session.patient_id}, Tipo: {session.questionnaire_type}, Score: {score}, Categoria: {category}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultado: {e}")
    
    def _get_status_message(self, session: QuestionnaireSession) -> str:
        """Retorna status da sessão atual"""
        try:
            progress = len(session.responses)
            total = {
                'uetg': 3,
                'gad7': 7,
                'phq9': 9, 
                'asrs18': 18
            }.get(session.questionnaire_type, 0)
            
            return f"📊 *Status do Questionário*\n\nTipo: {session.questionnaire_type.upper()}\nProgresso: {progress}/{total}\nIniciado: {session.started_at.strftime('%H:%M')}\nExpira: {session.expires_at.strftime('%H:%M')}"
            
        except Exception as e:
            logger.error(f"Erro ao gerar status: {e}")
            return "❌ Erro ao obter status."
    
    def cleanup_expired_sessions(self):
        """Remove sessões expiradas"""
        try:
            expired_phones = [
                phone for phone, session in self.active_sessions.items()
                if session.is_expired()
            ]
            
            for phone in expired_phones:
                del self.active_sessions[phone]
                logger.info(f"Sessão expirada removida: {phone}")
                
        except Exception as e:
            logger.error(f"Erro ao limpar sessões: {e}")

# Instância global do processador
response_processor = ResponseProcessor()
