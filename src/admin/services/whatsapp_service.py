import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AdminWhatsAppService:
    """Serviço WhatsApp para campanhas administrativas"""
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN', '').strip()
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '').strip()
        self.base_url = f"https://graph.facebook.com/v21.0/{self.phone_number_id}/messages"
        
    def send_template(self, phone_e164: str, template_name: str, lang_code: str = 'pt_BR', params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Enviar template WhatsApp
        
        Args:
            phone_e164: Número no formato E.164 (sem +)
            template_name: Nome do template aprovado
            lang_code: Código do idioma (default: pt_BR)
            params: Parâmetros do template {"1": "valor1", "2": "valor2"}
            
        Returns:
            Dict com resultado do envio
        """
        try:
            if not self.access_token or not self.phone_number_id:
                return {
                    'success': False,
                    'error': 'WhatsApp credentials not configured',
                    'wa_response': None
                }
            
            # Limpar telefone (garantir que não tem +)
            if phone_e164.startswith('+'):
                phone_e164 = phone_e164[1:]
            
            # Montar payload base
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_e164,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": lang_code}
                }
            }
            
            # Adicionar parâmetros se fornecidos
            if params:
                components = []
                
                # Parâmetros do body
                body_params = []
                for key in sorted(params.keys()):
                    body_params.append({
                        "type": "text",
                        "text": str(params[key])
                    })
                
                if body_params:
                    components.append({
                        "type": "body",
                        "parameters": body_params
                    })
                
                if components:
                    payload["template"]["components"] = components
            
            # Headers
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Log do envio (sem token)
            logger.info(f"Sending template {template_name} to {phone_e164[:4]}****{phone_e164[-4:]}")
            
            # Fazer requisição
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            # Processar resposta
            if response.status_code == 200:
                wa_response = response.json()
                message_id = wa_response.get('messages', [{}])[0].get('id')
                
                logger.info(f"Template sent successfully - Message ID: {message_id}")
                
                return {
                    'success': True,
                    'message_id': message_id,
                    'wa_response': wa_response,
                    'payload': payload
                }
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                
                logger.error(f"Template send failed: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'wa_response': error_data,
                    'payload': payload,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            logger.error("Template send timeout")
            return {
                'success': False,
                'error': 'Request timeout',
                'wa_response': None
            }
        except Exception as e:
            logger.error(f"Template send exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'wa_response': None
            }
    
    def validate_credentials(self) -> bool:
        """Validar se as credenciais estão configuradas"""
        return bool(self.access_token and self.phone_number_id)
    
    def get_phone_masked(self, phone_e164: str) -> str:
        """Retornar telefone mascarado para logs"""
        if len(phone_e164) >= 8:
            return f"{phone_e164[:4]}****{phone_e164[-4:]}"
        return "****"

