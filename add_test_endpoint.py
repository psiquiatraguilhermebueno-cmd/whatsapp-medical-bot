#!/usr/bin/env python3
"""
Adicionar endpoint de teste para envio direto de mensagem
"""

# Ler o arquivo main.py
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'r') as f:
    content = f.read()

# Adicionar endpoint de teste antes da linha final
test_endpoint = '''
@app.route("/api/test/send-direct/<phone_number>", methods=['POST'])
def test_send_direct(phone_number):
    """Endpoint para testar envio direto de mensagem"""
    try:
        data = request.get_json() or {}
        message = data.get('message', 'Teste de mensagem direta')
        
        print(f"🧪 TEST ENDPOINT: Sending message to {phone_number}")
        print(f"📝 Message: {message}")
        
        result = send_whatsapp_message(phone_number, message)
        
        return jsonify({
            "status": "success" if result else "failed",
            "message": f"Message {'sent' if result else 'failed'} to {phone_number}",
            "phone": phone_number,
            "text": message
        })
        
    except Exception as e:
        print(f"💥 Error in test endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

'''

# Encontrar onde inserir (antes do if __name__ == '__main__')
if 'if __name__ == \'__main__\':' in content:
    parts = content.split('if __name__ == \'__main__\':')
    new_content = parts[0] + test_endpoint + '\nif __name__ == \'__main__\':' + parts[1]
else:
    # Se não encontrar, adicionar no final
    new_content = content + test_endpoint

# Escrever o arquivo atualizado
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'w') as f:
    f.write(new_content)

print("✅ Endpoint de teste adicionado ao main.py")
