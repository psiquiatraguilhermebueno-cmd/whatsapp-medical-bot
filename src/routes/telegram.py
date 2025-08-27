from flask import Blueprint, request, jsonify
from src.services.telegram_service import TelegramService
from src.services.telegram_message_handler import TelegramMessageHandler
import logging
import os

telegram_bp = Blueprint('telegram', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instâncias dos serviços
telegram_service = TelegramService(bot_token=os.getenv('TELEGRAM_BOT_TOKEN'))
message_handler = TelegramMessageHandler()

@telegram_bp.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Webhook para receber atualizações do Telegram"""
    try:
        update = request.get_json()
        
        if not update:
            logger.warning("Webhook recebido sem dados")
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        logger.info(f"Webhook recebido: {update}")
        
        # Verificar se a atualização é válida
        if not telegram_service.is_valid_update(update):
            logger.warning("Atualização inválida recebida")
            return jsonify({"status": "error", "message": "Invalid update"}), 400
        
        # Processar a mensagem
        result = message_handler.handle_update(update)
        
        logger.info(f"Resultado do processamento: {result}")
        
        return jsonify({"status": "success", "result": result}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@telegram_bp.route('/set-webhook', methods=['POST'])
def set_webhook():
    """Configurar webhook do Telegram"""
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            return jsonify({"error": "webhook_url é obrigatório"}), 400
        
        result = telegram_service.set_webhook(webhook_url)
        
        if result.get('ok'):
            return jsonify({
                "message": "Webhook configurado com sucesso",
                "result": result
            }), 200
        else:
            return jsonify({
                "error": "Erro ao configurar webhook",
                "result": result
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao configurar webhook: {e}")
        return jsonify({"error": str(e)}), 500

@telegram_bp.route('/delete-webhook', methods=['POST'])
def delete_webhook():
    """Remover webhook do Telegram"""
    try:
        result = telegram_service.delete_webhook()
        
        if result.get('ok'):
            return jsonify({
                "message": "Webhook removido com sucesso",
                "result": result
            }), 200
        else:
            return jsonify({
                "error": "Erro ao remover webhook",
                "result": result
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao remover webhook: {e}")
        return jsonify({"error": str(e)}), 500

@telegram_bp.route('/bot-info', methods=['GET'])
def get_bot_info():
    """Obter informações do bot"""
    try:
        result = telegram_service.get_me()
        
        if result.get('ok'):
            return jsonify({
                "message": "Informações do bot obtidas com sucesso",
                "bot_info": result.get('result')
            }), 200
        else:
            return jsonify({
                "error": "Erro ao obter informações do bot",
                "result": result
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao obter informações do bot: {e}")
        return jsonify({"error": str(e)}), 500

@telegram_bp.route('/send-message', methods=['POST'])
def send_message():
    """Enviar mensagem via API (para testes)"""
    try:
        data = request.get_json()
        
        chat_id = data.get('chat_id')
        text = data.get('text')
        buttons = data.get('buttons')
        
        if not chat_id or not text:
            return jsonify({"error": "chat_id e text são obrigatórios"}), 400
        
        if buttons:
            result = telegram_service.send_interactive_message(chat_id, text, buttons)
        else:
            result = telegram_service.send_text_message(chat_id, text)
        
        if result.get('ok'):
            return jsonify({
                "message": "Mensagem enviada com sucesso",
                "result": result
            }), 200
        else:
            return jsonify({
                "error": "Erro ao enviar mensagem",
                "result": result
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return jsonify({"error": str(e)}), 500

@telegram_bp.route('/status', methods=['GET'])
def get_status():
    """Obter status da integração com Telegram"""
    try:
        # Verificar se o bot está funcionando
        bot_info = telegram_service.get_me()
        
        status = {
            "service": "Telegram Bot API",
            "status": "active" if bot_info.get('ok') else "error",
            "bot_token_configured": bool(telegram_service.bot_token and telegram_service.bot_token != "YOUR_BOT_TOKEN_HERE"),
            "webhook_configured": False,  # Seria verificado com getWebhookInfo
            "last_update": None
        }
        
        if bot_info.get('ok'):
            bot_data = bot_info.get('result', {})
            status.update({
                "bot_username": bot_data.get('username'),
                "bot_name": bot_data.get('first_name'),
                "bot_id": bot_data.get('id')
            })
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({"error": str(e)}), 500

@telegram_bp.route('/test-connection', methods=['GET'])
def test_connection():
    """Testar conexão com a API do Telegram"""
    try:
        result = telegram_service.get_me()
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            return jsonify({
                "status": "success",
                "message": "Conexão com Telegram estabelecida com sucesso",
                "bot_info": {
                    "username": bot_info.get('username'),
                    "name": bot_info.get('first_name'),
                    "id": bot_info.get('id'),
                    "can_join_groups": bot_info.get('can_join_groups'),
                    "can_read_all_group_messages": bot_info.get('can_read_all_group_messages'),
                    "supports_inline_queries": bot_info.get('supports_inline_queries')
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Erro ao conectar com Telegram",
                "error": result.get('description', 'Erro desconhecido')
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}")
        return jsonify({
            "status": "error",
            "message": "Erro ao testar conexão",
            "error": str(e)
        }), 500

