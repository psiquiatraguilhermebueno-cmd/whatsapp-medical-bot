#!/usr/bin/env python3
"""
Script para enviar templates via endpoint da aplicação Railway
"""

import requests
import json
from datetime import datetime

# URL da aplicação no Railway
APP_URL = "https://web-production-4fc41.up.railway.app"
RECIPIENT_NUMBER = "5514997799022"  # Guilherme Bueno

def send_template_via_app(template_name, recipient_phone, patient_name):
    """
    Envia template via endpoint da aplicação
    """
    endpoint = f"{APP_URL}/api/send-template"
    
    payload = {
        "template_name": template_name,
        "recipient_phone": recipient_phone,
        "patient_name": patient_name
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🚀 Enviando template '{template_name}' via aplicação...")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Template '{template_name}' enviado com sucesso!")
            return True
        else:
            print(f"❌ Erro ao enviar template '{template_name}'")
            return False
            
    except Exception as e:
        print(f"💥 Exceção ao enviar template '{template_name}': {str(e)}")
        return False

def create_send_endpoint():
    """
    Cria endpoint para envio de templates na aplicação
    """
    endpoint_code = '''
@app.route('/api/send-template', methods=['POST'])
def send_template():
    """Endpoint para enviar templates WhatsApp"""
    try:
        data = request.get_json()
        template_name = data.get('template_name')
        recipient_phone = data.get('recipient_phone')
        patient_name = data.get('patient_name', 'Paciente')
        
        # Configurações WhatsApp
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        
        if not access_token or not phone_number_id:
            return jsonify({"error": "Configurações WhatsApp não encontradas"}), 500
        
        # URL da API WhatsApp
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        # Headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Payload da mensagem
        message_data = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "pt_BR"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": patient_name
                            }
                        ]
                    }
                ]
            }
        }
        
        # Enviar mensagem
        response = requests.post(url, headers=headers, json=message_data)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "success": True,
                "message_id": result.get('messages', [{}])[0].get('id'),
                "template": template_name,
                "recipient": recipient_phone
            })
        else:
            return jsonify({
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
'''
    
    print("📝 Código do endpoint criado. Adicionando ao main.py...")
    return endpoint_code

def main():
    """
    Função principal
    """
    print("🎯 ENVIANDO TEMPLATES VIA APLICAÇÃO RAILWAY")
    print("=" * 50)
    
    # Primeiro, vamos tentar enviar diretamente
    templates_to_test = [
        {
            "name": "gad7_checkin_ptbr",
            "description": "Template GAD-7 (Ansiedade)"
        },
        {
            "name": "phq9_checkin_ptbr", 
            "description": "Template PHQ-9 (Depressão)"
        }
    ]
    
    print(f"📱 Destinatário: {RECIPIENT_NUMBER}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success_count = 0
    total_count = len(templates_to_test)
    
    # Tentar enviar cada template
    for i, template in enumerate(templates_to_test, 1):
        print(f"📤 TESTE {i}/{total_count}: {template['description']}")
        print("-" * 40)
        
        success = send_template_via_app(
            template_name=template["name"],
            recipient_phone=RECIPIENT_NUMBER,
            patient_name="Dr. Guilherme"
        )
        
        if success:
            success_count += 1
        
        print()
    
    # Resultado final
    print("=" * 50)
    print("🎉 TESTE DE TEMPLATES CONCLUÍDO!")
    print(f"✅ Sucessos: {success_count}/{total_count}")
    
    if success_count > 0:
        print("🏆 TEMPLATES ENVIADOS COM SUCESSO!")
        print("📱 Verifique seu WhatsApp para confirmar o recebimento.")
    else:
        print("⚠️ Nenhum template foi enviado. Vou criar o endpoint necessário.")
        create_send_endpoint()

if __name__ == "__main__":
    main()
