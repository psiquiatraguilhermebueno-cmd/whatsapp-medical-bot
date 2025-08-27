import os
import hmac
import hashlib
from flask import Blueprint, request, jsonify
from src.services.whatsapp_service import WhatsAppService
from src.services.message_handler import MessageHandler

whatsapp_bp = Blueprint('whatsapp', __name__)
whatsapp_service = WhatsAppService()
message_handler = MessageHandler()

def verify_webhook_signature(payload, signature):
    """
    Verificar assinatura X-Hub-Signature-256 do webhook
    """
    app_secret = os.environ.get('APP_SECRET')
    if not app_secret:
        print("WARNING: APP_SECRET não configurado - validação de webhook desabilitada")
        return True  # Permitir em desenvolvimento se não configurado
    
    if not signature:
        return False
    
    # Remover prefixo 'sha256=' se presente
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    # Calcular hash esperado
    expected_signature = hmac.new(
        app_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Comparação segura
    return hmac.compare_digest(expected_signature, signature)

@whatsapp_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verificar webhook do WhatsApp"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    verification_result = whatsapp_service.verify_webhook(mode, token, challenge)
    
    if verification_result:
        return verification_result, 200
    else:
        return 'Forbidden', 403

@whatsapp_bp.route('/webhook', methods=['POST'])
def receive_message():
    """Receber mensagens do WhatsApp via webhook"""
    try:
        # Obter dados brutos para validação de assinatura
        payload = request.get_data()
        signature = request.headers.get('X-Hub-Signature-256')
        
        # Validar assinatura do webhook
        if not verify_webhook_signature(payload, signature):
            print("SECURITY WARNING: Webhook signature validation failed")
            return jsonify({'status': 'error', 'message': 'Invalid signature'}), 403
        
        # Processar dados JSON
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        # Processar a mensagem
        parsed_message = whatsapp_service.parse_webhook_message(webhook_data)
        
        if parsed_message:
            # Marcar mensagem como lida
            whatsapp_service.mark_message_as_read(parsed_message['message_id'])
            
            # Processar a mensagem através do handler
            response = message_handler.handle_message(parsed_message)
            
            return jsonify({
                'status': 'success',
                'message': 'Message processed',
                'response': response
            }), 200
        
        return jsonify({'status': 'success', 'message': 'No message to process'}), 200
        
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@whatsapp_bp.route('/send-message', methods=['POST'])
def send_message():
    """Endpoint para enviar mensagens via API"""
    try:
        data = request.get_json()
        
        if not data or 'to' not in data or 'message' not in data:
            return jsonify({'error': 'Campos obrigatórios: to, message'}), 400
        
        to = whatsapp_service.format_phone_number(data['to'])
        message = data['message']
        
        result = whatsapp_service.send_text_message(to, message)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Message sent successfully',
                'response': result['response']
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send message',
                'error': result.get('error'),
                'response': result.get('response')
            }), result.get('status_code', 500)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@whatsapp_bp.route('/send-interactive', methods=['POST'])
def send_interactive():
    """Endpoint para enviar mensagens interativas"""
    try:
        data = request.get_json()
        
        required_fields = ['to', 'header', 'body', 'buttons']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos obrigatórios: to, header, body, buttons'}), 400
        
        to = whatsapp_service.format_phone_number(data['to'])
        header = data['header']
        body = data['body']
        buttons = data['buttons']
        
        result = whatsapp_service.send_interactive_message(to, header, body, buttons)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Interactive message sent successfully',
                'response': result['response']
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send interactive message',
                'error': result.get('error'),
                'response': result.get('response')
            }), result.get('status_code', 500)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@whatsapp_bp.route('/send-audio', methods=['POST'])
def send_audio():
    """Endpoint para enviar áudio"""
    try:
        data = request.get_json()
        
        if not data or 'to' not in data or 'audio_url' not in data:
            return jsonify({'error': 'Campos obrigatórios: to, audio_url'}), 400
        
        to = whatsapp_service.format_phone_number(data['to'])
        audio_url = data['audio_url']
        
        result = whatsapp_service.send_audio_message(to, audio_url)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Audio sent successfully',
                'response': result['response']
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send audio',
                'error': result.get('error'),
                'response': result.get('response')
            }), result.get('status_code', 500)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@whatsapp_bp.route('/test-connection', methods=['GET'])
def test_connection():
    """Testar conexão com a API do WhatsApp"""
    try:
        # Tentar fazer uma requisição simples para verificar a conexão
        test_number = "5511999999999"  # Número de teste
        test_message = "Teste de conexão - ignore esta mensagem"
        
        result = whatsapp_service.send_text_message(test_number, test_message)
        
        return jsonify({
            'status': 'connection_tested',
            'whatsapp_api_configured': bool(whatsapp_service.access_token and whatsapp_service.phone_number_id),
            'test_result': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'whatsapp_api_configured': bool(whatsapp_service.access_token and whatsapp_service.phone_number_id)
        }), 500

