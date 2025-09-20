#!/usr/bin/env python3
"""
Adicionar rotas u-ETG ao main.py
"""

# Ler arquivo main.py
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'r') as f:
    content = f.read()

# Adicionar rotas u-ETG
uetg_routes = '''
# ==================== ROTAS u-ETG ====================

@app.route("/api/uetg/generate-draw/<int:patient_id>", methods=['POST'])
def generate_uetg_draw(patient_id):
    """Gerar sorteio semanal para paciente"""
    try:
        from uetg_system import uetg
        
        draw_info = uetg.generate_weekly_draw(patient_id)
        
        if draw_info:
            # Enviar notificação para admin
            uetg.send_draw_notification_to_admin(draw_info)
            
            return jsonify({
                "status": "success",
                "message": "Sorteio gerado com sucesso",
                "draw_info": {
                    "first_date": draw_info['first_date'].isoformat(),
                    "second_date": draw_info['second_date'].isoformat(),
                    "patient_name": draw_info['patient_name']
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Não foi possível gerar sorteio"
            }), 400
            
    except Exception as e:
        print(f"💥 Error generating draw: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/uetg/add-patient", methods=['POST'])
def add_uetg_patient():
    """Adicionar paciente ao sistema u-ETG"""
    try:
        from uetg_system import uetg
        
        data = request.get_json()
        
        patient_id = uetg.add_patient(
            name=data['name'],
            phone_number=data['phone_number'],
            available_times=data.get('available_times', ["12:15", "16:40", "19:00"])
        )
        
        return jsonify({
            "status": "success",
            "message": "Paciente adicionado com sucesso",
            "patient_id": patient_id
        })
        
    except Exception as e:
        print(f"💥 Error adding u-ETG patient: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/uetg/schedule")
def get_uetg_schedule():
    """Obter agenda u-ETG da semana"""
    try:
        from uetg_system import uetg
        from datetime import datetime, timedelta
        
        # Calcular próxima segunda-feira
        today = datetime.now().date()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        schedule = uetg.get_weekly_schedule(next_monday)
        
        # Converter para formato JSON
        schedule_list = []
        for item in schedule:
            schedule_list.append({
                'draw_id': item[0],
                'patient_name': item[5],
                'first_date': item[3],
                'second_date': item[4],
                'first_time': item[7],
                'second_time': item[8]
            })
        
        return jsonify(schedule_list)
        
    except Exception as e:
        print(f"💥 Error getting u-ETG schedule: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/admin/uetg")
def uetg_admin():
    """Página administrativa do u-ETG"""
    return render_template('uetg_admin.html')
'''

# Adicionar processamento u-ETG no webhook
webhook_uetg_code = '''
        # Processar comandos u-ETG
        if message_text.lower() in ['agendar', 'consulta', 'uetg']:
            send_whatsapp_message(from_number, "Sistema u-ETG em desenvolvimento. Em breve você poderá agendar consultas por aqui!")
            return jsonify({"status": "ok"})
        
        # Processar seleção de horário u-ETG (formato HH:MM)
        import re
        if re.match(r'^\\d{1,2}:\\d{2}$', message_text):
            from uetg_system import uetg
            from datetime import datetime
            
            # Assumir que é para hoje (lógica pode ser melhorada)
            today = datetime.now().date()
            success = uetg.process_patient_time_selection(from_number, message_text, today)
            
            if success:
                print(f"✅ Horário {message_text} confirmado para {from_number}")
            
            return jsonify({"status": "ok"})
'''

# Encontrar onde inserir as rotas (antes das outras rotas administrativas)
if '# ==================== ROTAS ADMINISTRATIVAS ====================' in content:
    parts = content.split('# ==================== ROTAS ADMINISTRATIVAS ====================')
    new_content = parts[0] + uetg_routes + '\n\n# ==================== ROTAS ADMINISTRATIVAS ====================' + parts[1]
else:
    # Se não encontrar, adicionar antes do if __name__
    if 'if __name__ == \'__main__\':' in content:
        parts = content.split('if __name__ == \'__main__\':')
        new_content = parts[0] + uetg_routes + '\n\nif __name__ == \'__main__\':' + parts[1]
    else:
        new_content = content + '\n' + uetg_routes

# Adicionar processamento u-ETG no webhook
if 'if message_text.lower() == \'ajuda\':' in new_content:
    new_content = new_content.replace(
        'if message_text.lower() == \'ajuda\':',
        webhook_uetg_code + '\n        \n        if message_text.lower() == \'ajuda\':'
    )

# Escrever arquivo atualizado
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'w') as f:
    f.write(new_content)

print("✅ Rotas u-ETG adicionadas ao main.py")
