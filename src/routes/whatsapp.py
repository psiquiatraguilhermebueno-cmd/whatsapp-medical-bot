"""
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
