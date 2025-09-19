import os
import json
import requests
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Configurações WhatsApp
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')

# Estado dos questionários (em produção seria banco de dados)
questionnaire_states = {}

# Perguntas GAD-7
GAD7_QUESTIONS = [
    "Sentir-se nervoso, ansioso ou muito tenso?",
    "Não conseguir parar ou controlar as preocupações?",
    "Preocupar-se muito com diversas coisas?",
    "Ter dificuldade para relaxar?",
    "Ficar tão agitado que se torna difícil permanecer parado?",
    "Ficar facilmente aborrecido ou irritado?",
    "Sentir medo como se algo terrível fosse acontecer?"
]

# Significados das respostas
RESPONSE_MEANINGS = {
    "0": "Nenhuma vez",
    "1": "Vários dias",
    "2": "Mais da metade dos dias",
    "3": "Quase todos os dias"
}

def send_whatsapp_message(phone_number, message_text):
    """Envia mensagem de texto via WhatsApp"""
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("❌ WhatsApp credentials not configured")
        return False
    
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message_text}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            print(f"✅ Message sent to {phone_number}")
            return True
        else:
            print(f"❌ Error sending message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"💥 Exception sending message: {e}")
        return False

def start_gad7_questionnaire(phone_number):
    """Inicia questionário GAD-7"""
    questionnaire_states[phone_number] = {
        'type': 'gad7',
        'current_question': 0,
        'responses': [],
        'started_at': datetime.now().isoformat()
    }
    
    # Enviar instruções e primeira pergunta
    instructions = """📋 *QUESTIONÁRIO GAD-7 - ANSIEDADE*

Para cada pergunta, responda APENAS O NÚMERO:
• 0 = Nenhuma vez
• 1 = Vários dias  
• 2 = Mais da metade dos dias
• 3 = Quase todos os dias

Exemplo: Se a resposta for "Vários dias", digite apenas: 1

---

*PERGUNTA 1/7*

Nas últimas 2 semanas, com que frequência você percebeu-se incomodado por:

*Sentir-se nervoso, ansioso ou muito tenso?*

Responda apenas o número: 0, 1, 2 ou 3"""
    
    return send_whatsapp_message(phone_number, instructions)

def process_gad7_response(phone_number, response_text):
    """Processa resposta do GAD-7"""
    if phone_number not in questionnaire_states:
        return send_whatsapp_message(phone_number, "❌ Questionário não encontrado. Digite 'gad7' para iniciar.")
    
    state = questionnaire_states[phone_number]
    
    # Validar resposta
    if response_text not in ['0', '1', '2', '3']:
        return send_whatsapp_message(phone_number, 
            f"❌ Resposta inválida. Por favor, responda apenas: 0, 1, 2 ou 3")
    
    # Salvar resposta
    state['responses'].append(int(response_text))
    current_q = state['current_question']
    
    # Feedback da resposta
    meaning = RESPONSE_MEANINGS[response_text]
    feedback = f"✅ Registrado. Você assinalou: {response_text} - {meaning}"
    
    # Próxima pergunta ou resultado final
    state['current_question'] += 1
    
    if state['current_question'] < len(GAD7_QUESTIONS):
        # Próxima pergunta
        next_q = state['current_question']
        next_question = f"""
*PERGUNTA {next_q + 1}/7*

Nas últimas 2 semanas, com que frequência você percebeu-se incomodado por:

*{GAD7_QUESTIONS[next_q]}*

Responda apenas o número: 0, 1, 2 ou 3"""
        
        message = feedback + next_question
    else:
        # Calcular resultado final
        total_score = sum(state['responses'])
        
        # Categorizar resultado
        if total_score <= 4:
            category = "Ansiedade mínima"
            interpretation = "Seus sintomas de ansiedade estão em um nível muito baixo."
        elif total_score <= 9:
            category = "Ansiedade leve"
            interpretation = "Você apresenta sintomas leves de ansiedade."
        elif total_score <= 14:
            category = "Ansiedade moderada"
            interpretation = "Você apresenta sintomas moderados de ansiedade. Considere conversar com um profissional."
        else:
            category = "Ansiedade severa"
            interpretation = "Você apresenta sintomas severos de ansiedade. É recomendado buscar ajuda profissional."
        
        result_message = f"""
📊 *RESULTADO GAD-7*

*Pontuação total:* {total_score}/21
*Categoria:* {category}

*Interpretação:* {interpretation}

*Suas respostas:*
"""
        
        for i, response in enumerate(state['responses']):
            result_message += f"Pergunta {i+1}: {response} - {RESPONSE_MEANINGS[str(response)]}\n"
        
        result_message += f"""
*Data:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Obrigado por responder o questionário! 🙏"""
        
        message = feedback + result_message
        
        # Limpar estado
        del questionnaire_states[phone_number]
    
    return send_whatsapp_message(phone_number, message)

@app.route("/")
def index():
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "running",
        "version": "1.0.0",
        "features": ["gad7_questionnaire"]
    })

@app.route("/health")
def health():
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "healthy",
        "version": "1.0.0",
        "database": "ok",
        "admin_enabled": True,
        "whatsapp_configured": bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)
    })

@app.route("/api/whatsapp/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    """Webhook do WhatsApp"""
    
    if request.method == "GET":
        # Verificação do webhook
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            print("✅ Webhook verified")
            return challenge
        else:
            print("❌ Webhook verification failed")
            return "Verification failed", 403
    
    elif request.method == "POST":
        # Processar mensagem recebida
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
                        # Extrair informações da mensagem
                        phone_number = message.get('from')
                        message_type = message.get('type')
                        
                        if message_type == 'text':
                            text_body = message.get('text', {}).get('body', '').strip().lower()
                            
                            print(f"📱 Received from {phone_number}: {text_body}")
                            
                            # Comandos especiais
                            if text_body == 'gad7':
                                start_gad7_questionnaire(phone_number)
                            elif phone_number in questionnaire_states:
                                # Processar resposta do questionário
                                process_gad7_response(phone_number, text_body)
                            else:
                                # Mensagem de ajuda
                                help_message = """👋 Olá! Sou o assistente da Clínica Dr. Guilherme.

Comandos disponíveis:
• Digite *gad7* para iniciar o questionário de ansiedade

Como posso ajudá-lo hoje?"""
                                send_whatsapp_message(phone_number, help_message)
            
            return jsonify({"status": "ok"})
            
        except Exception as e:
            print(f"💥 Error processing webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/test/gad7/<phone_number>")
def test_gad7(phone_number):
    """Endpoint para testar GAD-7"""
    if start_gad7_questionnaire(phone_number):
        return jsonify({"status": "success", "message": f"GAD-7 started for {phone_number}"})
    else:
        return jsonify({"status": "error", "message": "Failed to start GAD-7"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    print(f"🚀 Starting WhatsApp Medical Bot on port {port}")
    print(f"📱 WhatsApp configured: {bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)}")
    print(f"🔗 Webhook URL: https://your-domain.com/api/whatsapp/webhook")
    print(f"💊 Health check: https://your-domain.com/health")
    
    app.run(host="0.0.0.0", port=port, debug=False)
