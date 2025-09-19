#!/usr/bin/env python3
"""
Script para adicionar endpoint de envio de templates ao main.py
"""

def add_send_endpoint():
    """
    Adiciona endpoint de envio de templates ao main.py
    """
    
    # Ler o arquivo main.py atual
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Endpoint para adicionar
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
                "recipient": recipient_phone,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-templates', methods=['POST'])
def test_templates():
    """Endpoint para testar múltiplos templates"""
    try:
        data = request.get_json()
        recipient_phone = data.get('recipient_phone', '5514997799022')
        patient_name = data.get('patient_name', 'Dr. Guilherme')
        
        templates = [
            'gad7_checkin_ptbr',
            'phq9_checkin_ptbr'
        ]
        
        results = []
        
        for template in templates:
            # Fazer requisição interna para enviar template
            template_data = {
                'template_name': template,
                'recipient_phone': recipient_phone,
                'patient_name': patient_name
            }
            
            # Simular envio (usar a função send_template diretamente)
            try:
                access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
                phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
                
                url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                message_data = {
                    "messaging_product": "whatsapp",
                    "to": recipient_phone,
                    "type": "template",
                    "template": {
                        "name": template,
                        "language": {"code": "pt_BR"},
                        "components": [{
                            "type": "body",
                            "parameters": [{"type": "text", "text": patient_name}]
                        }]
                    }
                }
                
                response = requests.post(url, headers=headers, json=message_data)
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "template": template,
                        "success": True,
                        "message_id": result.get('messages', [{}])[0].get('id')
                    })
                else:
                    results.append({
                        "template": template,
                        "success": False,
                        "error": response.text
                    })
                    
            except Exception as e:
                results.append({
                    "template": template,
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "total_sent": len([r for r in results if r['success']]),
            "total_templates": len(templates)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
'''
    
    # Verificar se o endpoint já existe
    if '/api/send-template' in content:
        print("✅ Endpoint já existe no main.py")
        return True
    
    # Adicionar imports necessários se não existirem
    imports_to_add = []
    if 'from datetime import datetime' not in content:
        imports_to_add.append('from datetime import datetime')
    if 'import requests' not in content:
        imports_to_add.append('import requests')
    
    # Encontrar onde adicionar os imports
    if imports_to_add:
        import_section = content.find('from flask import')
        if import_section != -1:
            # Encontrar o final da seção de imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from flask import'):
                    # Adicionar imports após esta linha
                    for imp in imports_to_add:
                        lines.insert(i + 1, imp)
                    break
            content = '\n'.join(lines)
    
    # Adicionar o endpoint antes da linha final do arquivo
    if 'if __name__ == "__main__":' in content:
        content = content.replace('if __name__ == "__main__":', endpoint_code + '\n\nif __name__ == "__main__":')
    else:
        content += endpoint_code
    
    # Escrever o arquivo atualizado
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Endpoint de envio de templates adicionado ao main.py")
    return True

if __name__ == "__main__":
    print("🔧 Adicionando endpoint de envio de templates...")
    add_send_endpoint()
    print("🎉 Endpoint adicionado com sucesso!")
