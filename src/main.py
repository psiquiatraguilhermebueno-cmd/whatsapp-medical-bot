import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# Carregar variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

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
    """Envia mensagem de texto via WhatsApp com logs detalhados"""
    print(f"🔄 Attempting to send message to {phone_number}")
    print(f"📝 Message length: {len(message_text)} characters")
    
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("❌ WhatsApp credentials not configured")
        print(f"Token exists: {bool(WHATSAPP_ACCESS_TOKEN)}")
        print(f"Phone ID exists: {bool(WHATSAPP_PHONE_NUMBER_ID)}")
        return False
    
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    print(f"🌐 API URL: {url}")
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN[:20]}...',  # Log partial token
        'Content-Type': 'application/json'
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message_text}
    }
    
    print(f"📤 Sending data: {json.dumps(data, indent=2)}")
    
    # Tentar enviar até 3 vezes
    for attempt in range(3):
        try:
            print(f"🔄 Attempt {attempt + 1}/3")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"📊 Response status: {response.status_code}")
            print(f"📝 Response headers: {dict(response.headers)}")
            print(f"📄 Response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                print(f"✅ Message sent successfully to {phone_number} - ID: {message_id}")
                return True
            else:
                print(f"❌ Error sending message: {response.status_code}")
                print(f"Error details: {response.text}")
                
                # Se for erro 400, não tentar novamente
                if response.status_code == 400:
                    break
                    
        except Exception as e:
            print(f"💥 Exception on attempt {attempt + 1}: {e}")
            if attempt == 2:  # Última tentativa
                return False
            
        # Aguardar antes da próxima tentativa
        if attempt < 2:
            import time
            time.sleep(2)
    
    print(f"❌ Failed to send message after 3 attempts")
    return False

def send_whatsapp_buttons(phone_number, message_text, buttons):
    """Envia mensagem com botões via WhatsApp"""
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
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": message_text},
            "action": {
                "buttons": buttons
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown')
            print(f"✅ Interactive message sent to {phone_number} - ID: {message_id}")
            return True
        else:
            print(f"❌ Error sending interactive message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"💥 Exception sending interactive message: {e}")
        return False

def send_gad7_invitation(phone_number):
    """Envia convite para GAD-7 com botões"""
    message_text = """Olá! Sou o assistente da *Clínica Dr. Guilherme*.

Vamos preencher a escala GAD-7 para monitorar como ficou a sua ansiedade?

O questionário tem 7 perguntas rápidas sobre as últimas 2 semanas."""
    
    buttons = [
        {
            "type": "reply",
            "reply": {
                "id": "start_gad7",
                "title": "🚀 COMEÇAR"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "stop_gad7",
                "title": "⏹️ PARAR"
            }
        }
    ]
    
    return send_whatsapp_buttons(phone_number, message_text, buttons)

def start_gad7_questionnaire(phone_number):
    """Inicia questionário GAD-7 após clique em COMEÇAR"""
    questionnaire_states[phone_number] = {
        'type': 'gad7',
        'current_question': 0,
        'responses': [],
        'started_at': datetime.now().isoformat()
    }
    
    print(f"🚀 Starting GAD-7 for {phone_number}")
    
    # Enviar instruções e primeira pergunta juntas
    complete_message = """📋 *INSTRUÇÕES GAD-7*

Para cada pergunta, responda APENAS O NÚMERO:
• 0 = Nenhuma vez
• 1 = Vários dias  
• 2 = Mais da metade dos dias
• 3 = Quase todos os dias

Digite *cancelar* a qualquer momento para interromper.

---

*PERGUNTA 1/7*

Nas últimas 2 semanas, com que frequência você percebeu-se incomodado por:

*Sentir-se nervoso, ansioso ou muito tenso?*

Responda apenas o número: 0, 1, 2 ou 3"""
    
    print(f"📤 Sending complete message to {phone_number}")
    result = send_whatsapp_message(phone_number, complete_message)
    print(f"📊 Send result: {result}")
    
    return result

def cancel_questionnaire(phone_number):
    """Cancela questionário em andamento"""
    if phone_number in questionnaire_states:
        del questionnaire_states[phone_number]
        print(f"⏹️ Questionnaire cancelled for {phone_number}")
        return send_whatsapp_message(phone_number, "❌ Questionário cancelado. Digite *gad7* se quiser tentar novamente.")
    else:
        return send_whatsapp_message(phone_number, "ℹ️ Nenhum questionário ativo para cancelar.")

def process_gad7_response(phone_number, response_text):
    """Processa resposta do GAD-7"""
    if phone_number not in questionnaire_states:
        return send_whatsapp_message(phone_number, "❌ Questionário não encontrado. Digite *gad7* para iniciar.")
    
    state = questionnaire_states[phone_number]
    
    print(f"🔍 Processing GAD-7 response from {phone_number}: '{response_text}'")
    
    # Validar resposta
    if response_text not in ['0', '1', '2', '3']:
        return send_whatsapp_message(phone_number, 
            f"❌ Resposta inválida. Por favor, responda apenas: 0, 1, 2 ou 3\n\nOu digite *cancelar* para interromper.")
    
    # Salvar resposta
    state['responses'].append(int(response_text))
    current_q = state['current_question']
    
    print(f"✅ Response {response_text} saved for question {current_q + 1}")
    
    # Feedback da resposta
    meaning = RESPONSE_MEANINGS[response_text]
    feedback = f"✅ Registrado. Você assinalou: {response_text} - {meaning}"
    
    # Próxima pergunta ou resultado final
    state['current_question'] += 1
    
    print(f"🔄 Updated state: question {state['current_question']}, total questions: {len(GAD7_QUESTIONS)}")
    
    if state['current_question'] < len(GAD7_QUESTIONS):
        # Próxima pergunta
        next_q = state['current_question']
        next_question = f"""

*PERGUNTA {next_q + 1}/7*

Nas últimas 2 semanas, com que frequência você percebeu-se incomodado por:

*{GAD7_QUESTIONS[next_q]}*

Responda apenas o número: 0, 1, 2 ou 3
(Digite *cancelar* para interromper)"""
        
        message = feedback + next_question
        print(f"📤 Sending question {next_q + 1}/7 to {phone_number}")
        print(f"📝 Message content: {message[:100]}...")
        
        # Enviar mensagem e verificar resultado
        result = send_whatsapp_message(phone_number, message)
        print(f"📊 Message send result: {result}")
        return result
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

Obrigado por responder o questionário! 🙏

Digite *gad7* para fazer um novo questionário."""
        
        message = feedback + result_message
        
        print(f"📊 GAD-7 completed. Score: {total_score}/21 - {category}")
        
        # Limpar estado
        del questionnaire_states[phone_number]
    
    return send_whatsapp_message(phone_number, message)


# VERSÃO DE EMERGÊNCIA - GAD-7 VIA TEXTO SIMPLES

def emergency_gad7_handler(phone_number, text_body):
    """Handler de emergência para GAD-7 via texto simples"""
    text_lower = text_body.lower().strip()
    
    # Comandos especiais
    # Tentar handler de emergência primeiro
    if emergency_gad7_handler(phone_number, text_body):
        return True
    
    if text_lower == 'gad7':
        # Enviar todas as perguntas de uma vez
        all_questions = """📋 *QUESTIONÁRIO GAD-7 COMPLETO*

Responda TODAS as 7 perguntas abaixo com números de 0 a 3:
• 0 = Nenhuma vez
• 1 = Vários dias  
• 2 = Mais da metade dos dias
• 3 = Quase todos os dias

*FORMATO DE RESPOSTA:* Digite os 7 números separados por espaço
Exemplo: 1 2 0 3 1 2 1

*PERGUNTAS:*

1. Sentir-se nervoso, ansioso ou muito tenso?
2. Não conseguir parar ou controlar as preocupações?
3. Preocupar-se muito com diversas coisas?
4. Ter dificuldade para relaxar?
5. Ficar tão agitado que se torna difícil permanecer parado?
6. Ficar facilmente aborrecido ou irritado?
7. Sentir medo como se algo terrível fosse acontecer?

*Responda com 7 números separados por espaço.*"""
        
        return send_whatsapp_message(phone_number, all_questions)
    
    # Verificar se é resposta do GAD-7 (7 números)
    if text_body.strip() and all(c.isdigit() or c.isspace() for c in text_body.strip()):
        numbers = text_body.strip().split()
        
        if len(numbers) == 7 and all(n in ['0', '1', '2', '3'] for n in numbers):
            # Processar resposta completa
            total_score = sum(int(n) for n in numbers)
            
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
            
            result_message = f"""📊 *RESULTADO GAD-7*

*Suas respostas:* {' '.join(numbers)}
*Pontuação total:* {total_score}/21
*Categoria:* {category}

*Interpretação:* {interpretation}

*Data:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Obrigado por responder o questionário! 🙏

Digite *gad7* para fazer um novo questionário."""
            
            return send_whatsapp_message(phone_number, result_message)
    
    return False


def process_text_message(phone_number, text_body):
    """Processa mensagens de texto"""
    text_lower = text_body.lower().strip()
    
    print(f"📝 Processing text: '{text_body}' from {phone_number}")
    
    # Comandos de cancelamento (prioridade máxima)
    if text_lower in ['cancelar', 'parar', 'sair', 'stop', 'cancel']:
        print(f"⏹️ Cancel command received: {text_lower}")
        return cancel_questionnaire(phone_number)
    
    # Comandos específicos
    # Tentar handler de emergência primeiro
    if emergency_gad7_handler(phone_number, text_body):
        return True
    
    if text_lower == 'gad7':
        print("📋 GAD-7 questionnaire requested - STARTING DIRECTLY")
        return start_gad7_questionnaire(phone_number)
    
    # Se há questionário ativo, processar resposta
    elif phone_number in questionnaire_states:
        print(f"🔄 Processing questionnaire response")
        return process_gad7_response(phone_number, text_body)
    
    # Mensagem de ajuda
    else:
        help_message = """👋 Olá! Sou o assistente da *Clínica Dr. Guilherme*.

*Comandos disponíveis:*
• Digite *gad7* para iniciar o questionário de ansiedade
• Digite *cancelar* para interromper questionário em andamento

Como posso ajudá-lo hoje?"""
        return send_whatsapp_message(phone_number, help_message)

@app.route("/")
def index():
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "running",
        "version": "1.1.0",
        "features": ["gad7_questionnaire", "interactive_buttons", "cancel_commands"]
    })

@app.route("/health")
def health():
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "healthy",
        "version": "1.1.0",
        "database": "ok",
        "admin_enabled": True,
        "whatsapp_configured": bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID),
        "active_questionnaires": len(questionnaire_states)
    })

@app.route("/api/whatsapp/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    """Webhook do WhatsApp"""
    
    if request.method == "GET":
        # Verificação do webhook
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        print(f"🔍 Webhook verification: mode={mode}, token={token}")
        
        if mode == "subscribe" and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            print("✅ Webhook verified successfully")
            return challenge
        else:
            print("❌ Webhook verification failed")
            return "Verification failed", 403
    
    elif request.method == "POST":
        # Processar mensagem recebida
        try:
            data = request.get_json()
            print(f"📥 Webhook received: {json.dumps(data, indent=2)}")
            
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
                        
                        print(f"📱 Message from {phone_number}, type: {message_type}")
                        
                        if message_type == 'text':
                            text_body = message.get('text', {}).get('body', '').strip()
                            process_text_message(phone_number, text_body)
                        
                        elif message_type == 'interactive':
                            # Processar botões interativos
                            interactive = message.get('interactive', {})
                            button_reply = interactive.get('button_reply', {})
                            button_id = button_reply.get('id')
                            
                            print(f"🔘 Button pressed: {button_id}")
                            
                            if button_id == 'start_gad7':
                                print("🚀 Starting GAD-7 questionnaire")
                                start_gad7_questionnaire(phone_number)
                            elif button_id == 'stop_gad7':
                                print("⏹️ Stopping GAD-7")
                                cancel_questionnaire(phone_number)
            
            return jsonify({"status": "ok"})
            
        except Exception as e:
            print(f"💥 Error processing webhook: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/test/gad7/<phone_number>")
def test_gad7(phone_number):
    """Endpoint para testar GAD-7"""
    if send_gad7_invitation(phone_number):
        return jsonify({"status": "success", "message": f"GAD-7 invitation sent to {phone_number}"})
    else:
        return jsonify({"status": "error", "message": "Failed to send GAD-7 invitation"}), 500

@app.route("/api/debug/states")
def debug_states():
    """Debug endpoint para ver estados dos questionários"""
    return jsonify({
        "active_questionnaires": len(questionnaire_states),
        "states": {phone: {
            "type": state["type"],
            "current_question": state["current_question"],
            "responses_count": len(state["responses"]),
            "started_at": state["started_at"]
        } for phone, state in questionnaire_states.items()}
    })

@app.route("/api/debug/clear")
def clear_states():
    """Endpoint para limpar todos os estados (debug)"""
    global questionnaire_states
    count = len(questionnaire_states)
    questionnaire_states = {}
    return jsonify({"status": "success", "message": f"Cleared {count} questionnaire states"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    print(f"🚀 Starting WhatsApp Medical Bot v1.1.0 on port {port}")
    print(f"📱 WhatsApp configured: {bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)}")
    print(f"🔗 Webhook URL: https://web-production-4fc41.up.railway.app/api/whatsapp/webhook")
    print(f"💊 Health check: https://web-production-4fc41.up.railway.app/health")
    print(f"🐛 Debug states: https://web-production-4fc41.up.railway.app/api/debug/states")
    print(f"🧹 Clear states: https://web-production-4fc41.up.railway.app/api/debug/clear")
    
    app.run(host="0.0.0.0", port=port, debug=False)

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

