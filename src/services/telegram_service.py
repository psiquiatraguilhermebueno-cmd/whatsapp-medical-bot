import requests
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import quote

class TelegramService:
    """Serviço para integração com a API do Telegram Bot"""
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or "YOUR_BOT_TOKEN_HERE"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.logger = logging.getLogger(__name__)
    
    def send_text_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> Dict:
        """
        Enviar mensagem de texto
        
        Args:
            chat_id: ID do chat do Telegram
            text: Texto da mensagem
            parse_mode: Formato do texto (Markdown ou HTML)
            
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao enviar mensagem: {e}")
            return {"ok": False, "error": str(e)}
    
    def send_interactive_message(self, chat_id: str, text: str, buttons: List[Dict], parse_mode: str = "Markdown") -> Dict:
        """
        Enviar mensagem com botões interativos (inline keyboard)
        
        Args:
            chat_id: ID do chat
            text: Texto da mensagem
            buttons: Lista de botões [{"text": "Texto", "callback_data": "dados"}]
            parse_mode: Formato do texto
            
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/sendMessage"
        
        # Converter botões para formato do Telegram
        keyboard = []
        for button in buttons:
            keyboard.append([{
                "text": button.get("text", button.get("title", "Botão")),
                "callback_data": button.get("callback_data", button.get("id", "button"))
            }])
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao enviar mensagem interativa: {e}")
            return {"ok": False, "error": str(e)}
    
    def send_audio_message(self, chat_id: str, audio_url: str, caption: str = None) -> Dict:
        """
        Enviar mensagem de áudio
        
        Args:
            chat_id: ID do chat
            audio_url: URL do arquivo de áudio
            caption: Legenda do áudio
            
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/sendAudio"
        
        payload = {
            "chat_id": chat_id,
            "audio": audio_url
        }
        
        if caption:
            payload["caption"] = caption
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao enviar áudio: {e}")
            return {"ok": False, "error": str(e)}
    
    def send_document(self, chat_id: str, document_url: str, caption: str = None) -> Dict:
        """
        Enviar documento
        
        Args:
            chat_id: ID do chat
            document_url: URL do documento
            caption: Legenda do documento
            
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/sendDocument"
        
        payload = {
            "chat_id": chat_id,
            "document": document_url
        }
        
        if caption:
            payload["caption"] = caption
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao enviar documento: {e}")
            return {"ok": False, "error": str(e)}
    
    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> Dict:
        """
        Responder a um callback query (clique em botão)
        
        Args:
            callback_query_id: ID do callback query
            text: Texto da resposta (opcional)
            show_alert: Se deve mostrar como alerta
            
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/answerCallbackQuery"
        
        payload = {
            "callback_query_id": callback_query_id
        }
        
        if text:
            payload["text"] = text
        
        if show_alert:
            payload["show_alert"] = True
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao responder callback: {e}")
            return {"ok": False, "error": str(e)}
    
    def edit_message_text(self, chat_id: str, message_id: int, text: str, buttons: List[Dict] = None, parse_mode: str = "Markdown") -> Dict:
        """
        Editar texto de uma mensagem existente
        
        Args:
            chat_id: ID do chat
            message_id: ID da mensagem
            text: Novo texto
            buttons: Novos botões (opcional)
            parse_mode: Formato do texto
            
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/editMessageText"
        
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if buttons:
            keyboard = []
            for button in buttons:
                keyboard.append([{
                    "text": button.get("text", button.get("title", "Botão")),
                    "callback_data": button.get("callback_data", button.get("id", "button"))
                }])
            
            payload["reply_markup"] = {
                "inline_keyboard": keyboard
            }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao editar mensagem: {e}")
            return {"ok": False, "error": str(e)}
    
    def get_chat_member(self, chat_id: str, user_id: int) -> Dict:
        """
        Obter informações de um membro do chat
        
        Args:
            chat_id: ID do chat
            user_id: ID do usuário
            
        Returns:
            Informações do membro
        """
        url = f"{self.base_url}/getChatMember"
        
        payload = {
            "chat_id": chat_id,
            "user_id": user_id
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao obter membro do chat: {e}")
            return {"ok": False, "error": str(e)}
    
    def set_webhook(self, webhook_url: str) -> Dict:
        """
        Configurar webhook para receber atualizações
        
        Args:
            webhook_url: URL do webhook
            
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/setWebhook"
        
        payload = {
            "url": webhook_url
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao configurar webhook: {e}")
            return {"ok": False, "error": str(e)}
    
    def delete_webhook(self) -> Dict:
        """
        Remover webhook
        
        Returns:
            Resposta da API do Telegram
        """
        url = f"{self.base_url}/deleteWebhook"
        
        try:
            response = requests.post(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao remover webhook: {e}")
            return {"ok": False, "error": str(e)}
    
    def get_me(self) -> Dict:
        """
        Obter informações do bot
        
        Returns:
            Informações do bot
        """
        url = f"{self.base_url}/getMe"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao obter informações do bot: {e}")
            return {"ok": False, "error": str(e)}
    
    def format_chat_id(self, chat_id: Any) -> str:
        """
        Formatar chat_id para string
        
        Args:
            chat_id: ID do chat (pode ser int ou string)
            
        Returns:
            Chat ID formatado como string
        """
        return str(chat_id)
    
    def extract_user_info(self, update: Dict) -> Dict:
        """
        Extrair informações do usuário de uma atualização
        
        Args:
            update: Atualização do Telegram
            
        Returns:
            Informações do usuário
        """
        user_info = {
            "chat_id": None,
            "user_id": None,
            "username": None,
            "first_name": None,
            "last_name": None,
            "full_name": None
        }
        
        # Extrair de mensagem
        if "message" in update:
            message = update["message"]
            if "from" in message:
                user = message["from"]
                user_info.update({
                    "chat_id": str(message["chat"]["id"]),
                    "user_id": user["id"],
                    "username": user.get("username"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name")
                })
        
        # Extrair de callback query
        elif "callback_query" in update:
            callback = update["callback_query"]
            if "from" in callback:
                user = callback["from"]
                user_info.update({
                    "chat_id": str(callback["message"]["chat"]["id"]),
                    "user_id": user["id"],
                    "username": user.get("username"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name")
                })
        
        # Montar nome completo
        if user_info["first_name"]:
            full_name = user_info["first_name"]
            if user_info["last_name"]:
                full_name += f" {user_info['last_name']}"
            user_info["full_name"] = full_name
        
        return user_info
    
    def is_valid_update(self, update: Dict) -> bool:
        """
        Verificar se a atualização é válida
        
        Args:
            update: Atualização do Telegram
            
        Returns:
            True se válida, False caso contrário
        """
        return "message" in update or "callback_query" in update
    
    def get_message_text(self, update: Dict) -> str:
        """
        Extrair texto da mensagem
        
        Args:
            update: Atualização do Telegram
            
        Returns:
            Texto da mensagem ou string vazia
        """
        if "message" in update and "text" in update["message"]:
            return update["message"]["text"]
        return ""
    
    def get_callback_data(self, update: Dict) -> str:
        """
        Extrair dados do callback query
        
        Args:
            update: Atualização do Telegram
            
        Returns:
            Dados do callback ou string vazia
        """
        if "callback_query" in update and "data" in update["callback_query"]:
            return update["callback_query"]["data"]
        return ""

