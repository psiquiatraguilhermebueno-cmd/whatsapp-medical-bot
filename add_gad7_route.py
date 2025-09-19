#!/usr/bin/env python3
"""
Adicionar rota para página GAD-7
"""

# Ler arquivo main.py
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'r') as f:
    content = f.read()

# Adicionar imports necessários
if 'from flask import Flask, request, jsonify' in content:
    content = content.replace(
        'from flask import Flask, request, jsonify',
        'from flask import Flask, request, jsonify, render_template, send_from_directory'
    )

# Adicionar rota para página GAD-7
gad7_routes = '''
@app.route("/questionario/gad7/<token>")
def gad7_questionnaire(token):
    """Página do questionário GAD-7"""
    # Aqui você validaria o token e carregaria dados do paciente
    return render_template('gad7.html')

@app.route("/static/<path:filename>")
def static_files(filename):
    """Servir arquivos estáticos"""
    return send_from_directory('static', filename)

@app.route("/api/save-gad7", methods=['POST'])
def save_gad7_result():
    """Salvar resultado do GAD-7"""
    try:
        data = request.get_json()
        
        # Aqui você salvaria no banco de dados
        print(f"📊 GAD-7 Result received:")
        print(f"Patient: {data['patient']['firstName']} {data['patient']['lastName']}")
        print(f"Score: {data['totalScore']}/21 - {data['category']}")
        print(f"Answers: {data['answers']}")
        
        return jsonify({
            "status": "success",
            "message": "Resultado salvo com sucesso"
        })
        
    except Exception as e:
        print(f"💥 Error saving GAD-7 result: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500
'''

# Encontrar onde inserir (antes do if __name__)
if 'if __name__ == \'__main__\':' in content:
    parts = content.split('if __name__ == \'__main__\':')
    new_content = parts[0] + gad7_routes + '\n\nif __name__ == \'__main__\':' + parts[1]
else:
    new_content = content + '\n' + gad7_routes

# Escrever arquivo atualizado
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'w') as f:
    f.write(new_content)

print("✅ Rotas GAD-7 adicionadas ao main.py")
