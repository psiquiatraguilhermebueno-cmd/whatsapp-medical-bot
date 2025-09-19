#!/usr/bin/env python3
"""
Script para enviar templates WhatsApp diretamente para teste
"""

import os
import requests
import json
from datetime import datetime

# Configurações do WhatsApp Business API
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Número do destinatário (Guilherme Bueno)
RECIPIENT_NUMBER = "5514997799022"

def send_whatsapp_template(template_name, recipient_phone, parameters=None):
    """
    Envia um template WhatsApp para um destinatário
    """
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Estrutura da mensagem template
    message_data = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "pt_BR"
            }
        }
    }
    
    # Adicionar parâmetros se fornecidos
    if parameters:
        message_data["template"]["components"] = [
            {
                "type": "body",
                "parameters": [
                    {
                        "type": "text",
                        "text": param
                    } for param in parameters
                ]
            }
        ]
    
    try:
        print(f"🚀 Enviando template '{template_name}' para {recipient_phone}...")
        print(f"📋 Dados: {json.dumps(message_data, indent=2)}")
        
        response = requests.post(
            WHATSAPP_API_URL,
            headers=headers,
            json=message_data,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'N/A')
            print(f"✅ Template '{template_name}' enviado com sucesso!")
            print(f"📧 Message ID: {message_id}")
            return True
        else:
            print(f"❌ Erro ao enviar template '{template_name}'")
            print(f"🔍 Detalhes: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exceção ao enviar template '{template_name}': {str(e)}")
        return False

def main():
    """
    Função principal para enviar templates de teste
    """
    print("🎯 INICIANDO TESTE DE TEMPLATES WHATSAPP")
    print("=" * 50)
    
    # Verificar variáveis de ambiente
    if not WHATSAPP_ACCESS_TOKEN:
        print("❌ WHATSAPP_ACCESS_TOKEN não encontrado!")
        return
    
    if not WHATSAPP_PHONE_NUMBER_ID:
        print("❌ WHATSAPP_PHONE_NUMBER_ID não encontrado!")
        return
    
    print(f"📱 Destinatário: {RECIPIENT_NUMBER}")
    print(f"🔑 Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Templates para testar
    templates_to_test = [
        {
            "name": "gad7_checkin_ptbr",
            "parameters": ["Dr. Guilherme"],
            "description": "Template GAD-7 (Ansiedade)"
        },
        {
            "name": "phq9_checkin_ptbr", 
            "parameters": ["Dr. Guilherme"],
            "description": "Template PHQ-9 (Depressão)"
        }
    ]
    
    success_count = 0
    total_count = len(templates_to_test)
    
    # Enviar cada template
    for i, template in enumerate(templates_to_test, 1):
        print(f"📤 TESTE {i}/{total_count}: {template['description']}")
        print("-" * 40)
        
        success = send_whatsapp_template(
            template_name=template["name"],
            recipient_phone=RECIPIENT_NUMBER,
            parameters=template["parameters"]
        )
        
        if success:
            success_count += 1
        
        print()
        
        # Aguardar entre envios
        if i < total_count:
            print("⏳ Aguardando 5 segundos antes do próximo envio...")
            import time
            time.sleep(5)
    
    # Resultado final
    print("=" * 50)
    print("🎉 TESTE DE TEMPLATES CONCLUÍDO!")
    print(f"✅ Sucessos: {success_count}/{total_count}")
    print(f"❌ Falhas: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🏆 TODOS OS TEMPLATES ENVIADOS COM SUCESSO!")
        print("📱 Verifique seu WhatsApp para confirmar o recebimento.")
    else:
        print("⚠️ Alguns templates falharam. Verifique os logs acima.")

if __name__ == "__main__":
    main()
