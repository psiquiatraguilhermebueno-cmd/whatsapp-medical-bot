import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class WhatsAppService:
    """Serviço para integração com WhatsApp Business API"""
    
    def __init__(self):
        # Configurações da API do WhatsApp Business
        # Estas variáveis devem ser configuradas no ambiente de produção
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
        self.webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'medical_bot_webhook_token')
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        
        # Headers para requisições
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_text_message(self, to: str, message: str) -> Dict:
        """Enviar mensagem de texto"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return {
                'success': response.status_code == 200,
                'response': response.json(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def send_interactive_message(self, to: str, header: str, body: str, buttons: List[Dict]) -> Dict:
        """Enviar mensagem interativa com botões"""
        url = f"{self.base_url}/messages"
        
        # Formatar botões para o formato da API
        formatted_buttons = []
        for i, button in enumerate(buttons):
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": button.get('id', f"btn_{i}"),
                    "title": button.get('title', f"Opção {i+1}")
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": header
                },
                "body": {
                    "text": body
                },
                "action": {
                    "buttons": formatted_buttons
                }
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return {
                'success': response.status_code == 200,
                'response': response.json(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def send_list_message(self, to: str, header: str, body: str, button_text: str, sections: List[Dict]) -> Dict:
        """Enviar mensagem com lista de opções"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": header
                },
                "body": {
                    "text": body
                },
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return {
                'success': response.status_code == 200,
                'response': response.json(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def send_audio_message(self, to: str, audio_url: str) -> Dict:
        """Enviar mensagem de áudio"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "audio",
            "audio": {
                "link": audio_url
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return {
                'success': response.status_code == 200,
                'response': response.json(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def send_document_message(self, to: str, document_url: str, filename: str, caption: str = "") -> Dict:
        """Enviar documento"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
                "caption": caption
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return {
                'success': response.status_code == 200,
                'response': response.json(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def mark_message_as_read(self, message_id: str) -> Dict:
        """Marcar mensagem como lida"""
        url = f"{self.base_url}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return {
                'success': response.status_code == 200,
                'response': response.json(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
    
    def parse_webhook_message(self, webhook_data: Dict) -> Optional[Dict]:
    """Processar mensagem recebida via webhook (robusto para campos None)"""
    try:
        entry = (webhook_data.get('entry') or [None])[0]
        if not entry:
            return None

        change = (entry.get('changes') or [None])[0]
        if not change or change.get('field') != 'messages':
            return None

        value = change.get('value') or {}
        messages = value.get('messages') or []
        contacts = value.get('contacts') or []
        if not messages:
            return None

        msg = messages[0]

        # helper: só faz strip se for string
        def s(v):
            return v.strip() if isinstance(v, str) else ''

        # nome do contato (pode não existir)
        contact_profile = (contacts[0].get('profile') if contacts else {}) or {}
        contact_name = s(contact_profile.get('name'))

        # pode ser None quando for botão/lista
        text_body = (msg.get('text') or {}).get('body')
        interactive = msg.get('interactive')  # dict ou None

        # tipo robusto
        if interactive:
            msg_type = 'interactive'
        elif isinstance(text_body, str) and text_body:
            msg_type = 'text'
        else:
            msg_type = msg.get('type')

        return {
            'message_id': msg.get('id'),
            'from': msg.get('from'),
            'timestamp': msg.get('timestamp'),
            'type': msg_type,
            'text': s(text_body),
            'interactive': interactive,
            'audio': msg.get('audio') if msg.get('type') == 'audio' else None,
            'document': msg.get('document') if msg.get('type') == 'document' else None,
            'image': msg.get('image') if msg.get('type') == 'image' else None,
            'video': msg.get('video') if msg.get('type') == 'video' else None,
            'contact_name': contact_name,
            'raw_data': webhook_data
        }
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return None
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verificar webhook do WhatsApp"""
        if mode == "subscribe" and token == self.webhook_verify_token:
            return challenge
        return None
    
    def format_phone_number(self, phone: str) -> str:
        """Formatar número de telefone para o padrão internacional"""
        # Remove caracteres não numéricos
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Se não começar com código do país, adiciona o código do Brasil (55)
        if not clean_phone.startswith('55') and len(clean_phone) >= 10:
            clean_phone = '55' + clean_phone
        
        return clean_phone

