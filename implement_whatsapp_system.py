#!/usr/bin/env python3
"""
Script para implementar sistema completo de templates WhatsApp e respostas automáticas
"""

import os
import json
from datetime import datetime

def create_whatsapp_templates():
    """Cria arquivo com templates WhatsApp para todos os questionários"""
    
    templates_content = '''"""
Templates WhatsApp para questionários médicos
"""

# Templates para u-ETG (Teste de Triagem de Uso de Álcool)
UETG_TEMPLATES = {
    "start": {
        "name": "uetg_start",
        "template": """🍺 *Teste u-ETG - Triagem de Uso de Álcool*

Olá! É hora do seu teste u-ETG.

Este teste ajuda a avaliar padrões de consumo de álcool.

*Responda com sinceridade:*

*1.* Com que frequência você consome bebidas alcoólicas?

a) Nunca (0 pontos)
b) Mensalmente ou menos (1 ponto)
c) 2-4 vezes por mês (2 pontos)
d) 2-3 vezes por semana (3 pontos)
e) 4 ou mais vezes por semana (4 pontos)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "question_2": {
        "template": """*2.* Quantas doses de álcool você consome num dia normal?

a) 1 ou 2 (0 pontos)
b) 3 ou 4 (1 ponto)
c) 5 ou 6 (2 pontos)
d) 7 a 9 (3 pontos)
e) 10 ou mais (4 pontos)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "question_3": {
        "template": """*3.* Com que frequência você consome seis ou mais doses em uma única ocasião?

a) Nunca (0 pontos)
b) Menos que mensalmente (1 ponto)
c) Mensalmente (2 pontos)
d) Semanalmente (3 pontos)
e) Quase diariamente (4 pontos)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "result_low": {
        "template": """✅ *Resultado u-ETG: BAIXO RISCO*

Pontuação: {score}/12

Seu padrão de consumo de álcool está dentro de limites considerados de baixo risco.

Continue mantendo esse padrão responsável! 👍

_Próximo teste em: {next_test}_"""
    },
    
    "result_medium": {
        "template": """⚠️ *Resultado u-ETG: RISCO MODERADO*

Pontuação: {score}/12

Seu padrão de consumo indica risco moderado. Considere:
• Reduzir a frequência de consumo
• Limitar a quantidade por ocasião
• Buscar atividades alternativas

_Próximo teste em: {next_test}_"""
    },
    
    "result_high": {
        "template": """🚨 *Resultado u-ETG: ALTO RISCO*

Pontuação: {score}/12

Seu padrão indica alto risco. Recomendações:
• Considere buscar ajuda profissional
• Reduza significativamente o consumo
• Converse com seu médico

_Próximo teste em: {next_test}_"""
    }
}

# Templates para GAD-7 (Transtorno de Ansiedade Generalizada)
GAD7_TEMPLATES = {
    "start": {
        "name": "gad7_start",
        "template": """😰 *Escala GAD-7 - Ansiedade*

Olá! É hora da sua avaliação de ansiedade GAD-7.

*Nas últimas 2 semanas, com que frequência você foi incomodado pelos seguintes problemas?*

*1.* Sentir-se nervoso, ansioso ou muito tenso

a) Nenhuma vez (0)
b) Vários dias (1)
c) Mais da metade dos dias (2)
d) Quase todos os dias (3)

Responda apenas com a letra (a, b, c ou d)""",
        "buttons": ["a", "b", "c", "d"]
    },
    
    "questions": [
        "Não conseguir parar ou controlar as preocupações",
        "Preocupar-se muito com diversas coisas",
        "Dificuldade para relaxar",
        "Ficar tão agitado que se torna difícil permanecer parado",
        "Ficar facilmente aborrecido ou irritado",
        "Sentir medo como se algo terrível fosse acontecer"
    ],
    
    "result_minimal": {
        "template": """✅ *Resultado GAD-7: ANSIEDADE MÍNIMA*

Pontuação: {score}/21

Seus níveis de ansiedade estão dentro do normal.

Continue cuidando do seu bem-estar mental! 😊

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_mild": {
        "template": """⚠️ *Resultado GAD-7: ANSIEDADE LEVE*

Pontuação: {score}/21

Você apresenta sintomas leves de ansiedade.

Dicas:
• Pratique técnicas de respiração
• Mantenha rotina de exercícios
• Considere técnicas de relaxamento

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_moderate": {
        "template": """🔶 *Resultado GAD-7: ANSIEDADE MODERADA*

Pontuação: {score}/21

Você apresenta sintomas moderados de ansiedade.

Recomendações:
• Converse com um profissional de saúde
• Pratique mindfulness
• Evite cafeína em excesso

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_severe": {
        "template": """🚨 *Resultado GAD-7: ANSIEDADE SEVERA*

Pontuação: {score}/21

Você apresenta sintomas severos de ansiedade.

*IMPORTANTE:* Procure ajuda profissional imediatamente.
• Converse com seu médico
• Considere terapia psicológica
• Não hesite em buscar suporte

_Próxima avaliação em: {next_test}_"""
    }
}

# Templates para PHQ-9 (Depressão)
PHQ9_TEMPLATES = {
    "start": {
        "name": "phq9_start",
        "template": """😔 *Escala PHQ-9 - Depressão*

Olá! É hora da sua avaliação de humor PHQ-9.

*Nas últimas 2 semanas, com que frequência você foi incomodado pelos seguintes problemas?*

*1.* Pouco interesse ou prazer em fazer as coisas

a) Nenhuma vez (0)
b) Vários dias (1)
c) Mais da metade dos dias (2)
d) Quase todos os dias (3)

Responda apenas com a letra (a, b, c ou d)""",
        "buttons": ["a", "b", "c", "d"]
    },
    
    "questions": [
        "Sentir-se desanimado, deprimido ou sem esperança",
        "Dificuldade para pegar no sono, continuar dormindo ou dormir demais",
        "Sentir-se cansado ou com pouca energia",
        "Falta de apetite ou comer demais",
        "Sentir-se mal consigo mesmo ou sentir que é um fracasso",
        "Dificuldade para se concentrar",
        "Lentidão para se mover ou falar, ou muito agitado",
        "Pensamentos de que seria melhor estar morto ou se ferir"
    ],
    
    "result_minimal": {
        "template": """✅ *Resultado PHQ-9: HUMOR NORMAL*

Pontuação: {score}/27

Seu humor está dentro da normalidade.

Continue cuidando da sua saúde mental! 😊

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_mild": {
        "template": """⚠️ *Resultado PHQ-9: DEPRESSÃO LEVE*

Pontuação: {score}/27

Você apresenta sintomas leves de depressão.

Dicas:
• Mantenha atividades prazerosas
• Pratique exercícios regularmente
• Mantenha contato social

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_moderate": {
        "template": """🔶 *Resultado PHQ-9: DEPRESSÃO MODERADA*

Pontuação: {score}/27

Você apresenta sintomas moderados de depressão.

Recomendações:
• Procure ajuda profissional
• Mantenha rotina estruturada
• Pratique autocuidado

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_severe": {
        "template": """🚨 *Resultado PHQ-9: DEPRESSÃO SEVERA*

Pontuação: {score}/27

Você apresenta sintomas severos de depressão.

*URGENTE:* Procure ajuda profissional imediatamente.
• Converse com seu médico
• Considere terapia
• Entre em contato com suporte de crise se necessário

_Próxima avaliação em: {next_test}_"""
    }
}

# Templates para ASRS-18 (TDAH)
ASRS18_TEMPLATES = {
    "start": {
        "name": "asrs18_start", 
        "template": """🧠 *Escala ASRS-18 - TDAH*

Olá! É hora da sua avaliação ASRS-18 para TDAH.

*Nos últimos 6 meses, com que frequência você teve os seguintes problemas?*

*1.* Dificuldade para se concentrar em trabalho ou atividades de lazer

a) Nunca (0)
b) Raramente (1)
c) Às vezes (2)
d) Frequentemente (3)
e) Muito frequentemente (4)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "questions": [
        "Dificuldade para organizar tarefas e atividades",
        "Problemas para lembrar de compromissos ou obrigações",
        "Evitar ou adiar tarefas que exigem muito esforço mental",
        "Inquietação com mãos ou pés ou se remexer na cadeira",
        "Sentir-se excessivamente ativo ou compelido a fazer coisas",
        "Cometer erros por falta de atenção quando tem que trabalhar",
        "Dificuldade para manter atenção em tarefas ou atividades",
        "Dificuldade para ouvir quando falam diretamente com você",
        "Não seguir instruções até o fim e não terminar trabalhos",
        "Dificuldade para brincar ou se envolver em atividades de lazer",
        "Estar 'a mil' ou sentir que tem um motor ligado",
        "Falar em excesso",
        "Terminar frases de pessoas que estão falando",
        "Dificuldade para esperar sua vez",
        "Interromper ou se intrometer em conversas",
        "Deixar seu lugar em situações onde deveria ficar sentado",
        "Sentir-se inquieto ou impaciente"
    ],
    
    "result_low": {
        "template": """✅ *Resultado ASRS-18: BAIXO RISCO TDAH*

Pontuação: {score}/72

Seus sintomas não indicam TDAH.

Continue mantendo suas estratégias de organização! 👍

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_moderate": {
        "template": """⚠️ *Resultado ASRS-18: RISCO MODERADO TDAH*

Pontuação: {score}/72

Você apresenta alguns sintomas de TDAH.

Dicas:
• Use listas e lembretes
• Organize seu ambiente
• Pratique técnicas de foco

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_high": {
        "template": """🔶 *Resultado ASRS-18: ALTO RISCO TDAH*

Pontuação: {score}/72

Você apresenta sintomas significativos de TDAH.

Recomendações:
• Procure avaliação com especialista
• Considere estratégias de organização
• Discuta opções de tratamento

_Próxima avaliação em: {next_test}_"""
    }
}

# Função para calcular pontuações
def calculate_scores():
    return {
        "uetg": {
            "low": (0, 3),
            "medium": (4, 7),
            "high": (8, 12)
        },
        "gad7": {
            "minimal": (0, 4),
            "mild": (5, 9),
            "moderate": (10, 14),
            "severe": (15, 21)
        },
        "phq9": {
            "minimal": (0, 4),
            "mild": (5, 9),
            "moderate": (10, 14),
            "severe": (15, 27)
        },
        "asrs18": {
            "low": (0, 23),
            "moderate": (24, 47),
            "high": (48, 72)
        }
    }

# Mensagens de boas-vindas e instruções
WELCOME_MESSAGES = {
    "first_contact": """👋 *Bem-vindo ao Bot Médico!*

Olá! Sou seu assistente para acompanhamento médico.

Você foi cadastrado para receber:
🍺 Teste u-ETG (álcool)
😰 Escala GAD-7 (ansiedade)  
😔 Escala PHQ-9 (depressão)
🧠 Escala ASRS-18 (TDAH)

Os questionários serão enviados conforme sua programação.

Para dúvidas, digite *ajuda*""",
    
    "help": """ℹ️ *Como funciona:*

• Você receberá questionários periodicamente
• Responda com sinceridade para melhor acompanhamento
• Use apenas as opções indicadas (a, b, c, d, e)
• Seus dados são confidenciais

*Comandos:*
• *ajuda* - Esta mensagem
• *status* - Ver próximos questionários
• *contato* - Falar com equipe médica

Em caso de emergência, procure atendimento médico imediato.""",
    
    "invalid_response": """❌ *Resposta inválida*

Por favor, responda apenas com a letra indicada (a, b, c, d ou e).

Se precisar de ajuda, digite *ajuda*""",
    
    "session_timeout": """⏰ *Sessão expirada*

O questionário foi interrompido por inatividade.

Você receberá um novo convite em breve.

Para dúvidas, digite *ajuda*"""
}
'''
    
    # Escreve o arquivo de templates
    with open('src/templates/whatsapp_templates.py', 'w', encoding='utf-8') as f:
        f.write(templates_content)
    
    print("✅ Templates WhatsApp criados em src/templates/whatsapp_templates.py")
    return True

def create_response_processor():
    """Cria processador de respostas automáticas"""
    
    processor_content = '''"""
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
                    return f"*{question_num + 1}.* {questions[question_num - 1]}\\n\\na) Nenhuma vez (0)\\nb) Vários dias (1)\\nc) Mais da metade dos dias (2)\\nd) Quase todos os dias (3)\\n\\nResponda apenas com a letra (a, b, c ou d)"
            
            elif session.questionnaire_type == 'asrs18':
                questions = ASRS18_TEMPLATES['questions']
                
                if question_num <= len(questions):
                    return f"*{question_num + 1}.* {questions[question_num - 1]}\\n\\na) Nunca (0)\\nb) Raramente (1)\\nc) Às vezes (2)\\nd) Frequentemente (3)\\ne) Muito frequentemente (4)\\n\\nResponda apenas com a letra (a, b, c, d ou e)"
            
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
            
            return f"📊 *Status do Questionário*\\n\\nTipo: {session.questionnaire_type.upper()}\\nProgresso: {progress}/{total}\\nIniciado: {session.started_at.strftime('%H:%M')}\\nExpira: {session.expires_at.strftime('%H:%M')}"
            
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
'''
    
    # Cria diretório se não existir
    os.makedirs('src/services', exist_ok=True)
    
    # Escreve o arquivo do processador
    with open('src/services/response_processor.py', 'w', encoding='utf-8') as f:
        f.write(processor_content)
    
    print("✅ Processador de respostas criado em src/services/response_processor.py")
    return True

def create_whatsapp_webhook():
    """Cria webhook integrado para WhatsApp"""
    
    webhook_content = '''"""
Webhook integrado para WhatsApp com processamento automático
"""

import json
import logging
import requests
from flask import Blueprint, request, jsonify
from src.services.response_processor import response_processor
from src.models.patient import Patient

logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp', __name__)

@whatsapp_bp.route('/api/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Webhook principal do WhatsApp"""
    
    if request.method == 'GET':
        return verify_webhook()
    elif request.method == 'POST':
        return handle_message()

def verify_webhook():
    """Verifica webhook do WhatsApp"""
    try:
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
            logger.info("Webhook verificado com sucesso")
            return challenge
        else:
            logger.warning("Token de verificação inválido")
            return "Token inválido", 403
            
    except Exception as e:
        logger.error(f"Erro na verificação do webhook: {e}")
        return "Erro interno", 500

def handle_message():
    """Processa mensagens recebidas"""
    try:
        data = request.get_json()
        
        if not data or 'entry' not in data:
            return jsonify({"status": "ok"})
        
        for entry in data['entry']:
            if 'changes' not in entry:
                continue
                
            for change in entry['changes']:
                if change.get('field') != 'messages':
                    continue
                
                value = change.get('value', {})
                messages = value.get('messages', [])
                
                for message in messages:
                    process_incoming_message(message, value)
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        return jsonify({"status": "error"}), 500

def process_incoming_message(message: dict, value: dict):
    """Processa mensagem individual"""
    try:
        # Extrai dados da mensagem
        phone = message.get('from')
        message_type = message.get('type')
        
        if message_type != 'text':
            return
        
        text = message.get('text', {}).get('body', '').strip()
        
        if not phone or not text:
            return
        
        logger.info(f"Mensagem recebida de {phone}: {text}")
        
        # Processa resposta
        response_text = response_processor.process_response(phone, text)
        
        if response_text:
            send_whatsapp_message(phone, response_text)
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem individual: {e}")

def send_whatsapp_message(phone: str, message: str) -> bool:
    """Envia mensagem via WhatsApp Business API"""
    try:
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        
        if not access_token or not phone_number_id:
            logger.error("Credenciais WhatsApp não configuradas")
            return False
        
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Mensagem enviada para {phone}")
            return True
        else:
            logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
        return False

def start_questionnaire_for_patient(patient_id: int, questionnaire_type: str) -> bool:
    """Inicia questionário para paciente específico"""
    try:
        # Busca dados do paciente
        patient = Patient.query.get(patient_id)
        if not patient:
            logger.error(f"Paciente {patient_id} não encontrado")
            return False
        
        phone = patient.phone_e164
        if not phone:
            logger.error(f"Telefone não encontrado para paciente {patient_id}")
            return False
        
        # Inicia questionário
        message = response_processor.start_questionnaire(patient_id, phone, questionnaire_type)
        
        # Envia primeira pergunta
        return send_whatsapp_message(phone, message)
        
    except Exception as e:
        logger.error(f"Erro ao iniciar questionário: {e}")
        return False
'''
    
    # Cria diretório se não existir
    os.makedirs('src/routes', exist_ok=True)
    
    # Escreve o arquivo do webhook
    with open('src/routes/whatsapp.py', 'w', encoding='utf-8') as f:
        f.write(webhook_content)
    
    print("✅ Webhook WhatsApp criado em src/routes/whatsapp.py")
    return True

def create_scheduler_integration():
    """Cria integração com scheduler para envio automático"""
    
    scheduler_content = '''"""
Integração com scheduler para envio automático de questionários
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from src.models.patient import Patient
from src.models.schedule import Schedule
from src.routes.whatsapp import start_questionnaire_for_patient

logger = logging.getLogger(__name__)

class QuestionnaireScheduler:
    """Gerencia agendamento automático de questionários"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Scheduler de questionários iniciado")
    
    def schedule_patient_questionnaires(self, patient_id: int):
        """Agenda questionários para um paciente"""
        try:
            patient = Patient.query.get(patient_id)
            if not patient:
                logger.error(f"Paciente {patient_id} não encontrado")
                return False
            
            schedules = Schedule.query.filter_by(patient_id=patient_id, active=True).all()
            
            for schedule in schedules:
                self._schedule_questionnaire(patient, schedule)
            
            logger.info(f"Questionários agendados para paciente {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao agendar questionários: {e}")
            return False
    
    def _schedule_questionnaire(self, patient: Patient, schedule: Schedule):
        """Agenda questionário específico"""
        try:
            job_id = f"patient_{patient.id}_{schedule.protocol_type}"
            
            # Remove job anterior se existir
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Calcula próxima execução
            next_run = self._calculate_next_run(schedule)
            
            if schedule.frequency == 'daily':
                self.scheduler.add_job(
                    func=self._send_questionnaire,
                    trigger='cron',
                    hour=int(schedule.time.split(':')[0]),
                    minute=int(schedule.time.split(':')[1]),
                    args=[patient.id, schedule.protocol_type],
                    id=job_id,
                    replace_existing=True
                )
            elif schedule.frequency == 'weekly':
                self.scheduler.add_job(
                    func=self._send_questionnaire,
                    trigger='cron',
                    day_of_week=0,  # Segunda-feira
                    hour=int(schedule.time.split(':')[0]),
                    minute=int(schedule.time.split(':')[1]),
                    args=[patient.id, schedule.protocol_type],
                    id=job_id,
                    replace_existing=True
                )
            elif schedule.frequency == 'monthly':
                self.scheduler.add_job(
                    func=self._send_questionnaire,
                    trigger='cron',
                    day=1,  # Primeiro dia do mês
                    hour=int(schedule.time.split(':')[0]),
                    minute=int(schedule.time.split(':')[1]),
                    args=[patient.id, schedule.protocol_type],
                    id=job_id,
                    replace_existing=True
                )
            elif schedule.frequency == 'random':
                # Para u-ETG: envio aleatório
                self._schedule_random_questionnaire(patient.id, schedule)
            
            logger.info(f"Questionário {schedule.protocol_type} agendado para paciente {patient.id}")
            
        except Exception as e:
            logger.error(f"Erro ao agendar questionário específico: {e}")
    
    def _schedule_random_questionnaire(self, patient_id: int, schedule: Schedule):
        """Agenda questionário com horário aleatório (u-ETG)"""
        try:
            import random
            
            # Gera horário aleatório entre 7h e 22h
            random_hour = random.randint(7, 22)
            random_minute = random.randint(0, 59)
            
            job_id = f"patient_{patient_id}_random_{schedule.protocol_type}"
            
            self.scheduler.add_job(
                func=self._send_questionnaire,
                trigger='cron',
                hour=random_hour,
                minute=random_minute,
                args=[patient_id, schedule.protocol_type],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"u-ETG agendado aleatoriamente para {random_hour:02d}:{random_minute:02d}")
            
        except Exception as e:
            logger.error(f"Erro ao agendar questionário aleatório: {e}")
    
    def _send_questionnaire(self, patient_id: int, questionnaire_type: str):
        """Envia questionário para paciente"""
        try:
            success = start_questionnaire_for_patient(patient_id, questionnaire_type)
            
            if success:
                logger.info(f"Questionário {questionnaire_type} enviado para paciente {patient_id}")
            else:
                logger.error(f"Falha ao enviar questionário {questionnaire_type} para paciente {patient_id}")
            
            # Reagenda próximo envio se necessário
            self._reschedule_if_needed(patient_id, questionnaire_type)
            
        except Exception as e:
            logger.error(f"Erro ao enviar questionário agendado: {e}")
    
    def _reschedule_if_needed(self, patient_id: int, questionnaire_type: str):
        """Reagenda questionário se necessário"""
        try:
            # Para questionários aleatórios, reagenda para próximo dia
            if questionnaire_type == 'uetg':
                schedule = Schedule.query.filter_by(
                    patient_id=patient_id,
                    protocol_type=questionnaire_type,
                    active=True
                ).first()
                
                if schedule and schedule.frequency == 'random':
                    # Reagenda para amanhã em horário aleatório
                    tomorrow = datetime.now() + timedelta(days=1)
                    self._schedule_random_questionnaire(patient_id, schedule)
            
        except Exception as e:
            logger.error(f"Erro ao reagendar questionário: {e}")
    
    def _calculate_next_run(self, schedule: Schedule) -> datetime:
        """Calcula próxima execução do questionário"""
        now = datetime.now()
        time_parts = schedule.time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if schedule.frequency == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif schedule.frequency == 'weekly':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = 0 - now.weekday()  # Segunda-feira
            if days_ahead <= 0:
                days_ahead += 7
            next_run += timedelta(days=days_ahead)
        elif schedule.frequency == 'monthly':
            next_run = now.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        else:
            next_run = now + timedelta(hours=1)
        
        return next_run
    
    def stop(self):
        """Para o scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler de questionários parado")

# Instância global do scheduler
questionnaire_scheduler = QuestionnaireScheduler()
'''
    
    # Escreve o arquivo do scheduler
    with open('src/services/questionnaire_scheduler.py', 'w', encoding='utf-8') as f:
        f.write(scheduler_content)
    
    print("✅ Scheduler de questionários criado em src/services/questionnaire_scheduler.py")
    return True

def main():
    """Função principal"""
    print("🚀 IMPLEMENTAÇÃO COMPLETA DO SISTEMA WHATSAPP")
    print("=" * 80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    success_count = 0
    total_tasks = 4
    
    # 1. Criar templates WhatsApp
    print("\n📝 CRIANDO TEMPLATES WHATSAPP...")
    os.makedirs('src/templates', exist_ok=True)
    if create_whatsapp_templates():
        success_count += 1
    
    # 2. Criar processador de respostas
    print("\n🤖 CRIANDO PROCESSADOR DE RESPOSTAS...")
    if create_response_processor():
        success_count += 1
    
    # 3. Criar webhook integrado
    print("\n🔗 CRIANDO WEBHOOK WHATSAPP...")
    if create_whatsapp_webhook():
        success_count += 1
    
    # 4. Criar scheduler de questionários
    print("\n⏰ CRIANDO SCHEDULER DE QUESTIONÁRIOS...")
    if create_scheduler_integration():
        success_count += 1
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DA IMPLEMENTAÇÃO")
    print("=" * 80)
    
    print(f"✅ Tarefas concluídas: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("\n🎉 SISTEMA WHATSAPP IMPLEMENTADO COM SUCESSO!")
        
        print("\n📋 COMPONENTES CRIADOS:")
        print("• Templates para u-ETG, GAD-7, PHQ-9, ASRS-18")
        print("• Processador de respostas automáticas")
        print("• Webhook integrado com WhatsApp Business API")
        print("• Scheduler automático de questionários")
        
        print("\n🔧 PRÓXIMOS PASSOS:")
        print("1. Fazer commit e push dos novos arquivos")
        print("2. Configurar templates no Facebook Business Manager")
        print("3. Testar webhook com mensagens reais")
        print("4. Registrar paciente Guilherme Bueno")
        print("5. Testar envio automático de questionários")
        
        print("\n📱 FUNCIONALIDADES IMPLEMENTADAS:")
        print("• Questionários interativos via WhatsApp")
        print("• Cálculo automático de pontuações")
        print("• Resultados personalizados por escala")
        print("• Agendamento automático por paciente")
        print("• Tratamento de sessões e timeouts")
        print("• Comandos de ajuda e status")
        
    else:
        print(f"\n❌ IMPLEMENTAÇÃO PARCIAL!")
        print(f"Apenas {success_count} de {total_tasks} tarefas foram concluídas")
    
    print(f"\n🔗 LINKS IMPORTANTES:")
    print(f"• Aplicação: https://web-production-4fc41.up.railway.app")
    print(f"• Painel Admin: https://web-production-4fc41.up.railway.app/admin")
    print(f"• Health Check: https://web-production-4fc41.up.railway.app/health")
    
    return success_count == total_tasks

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
