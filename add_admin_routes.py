#!/usr/bin/env python3
"""
Adicionar rotas administrativas ao main.py
"""

# Ler arquivo main.py
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'r') as f:
    content = f.read()

# Adicionar rotas administrativas
admin_routes = '''
# ==================== ROTAS ADMINISTRATIVAS ====================

@app.route("/admin")
def admin_dashboard():
    """Dashboard administrativo"""
    # Aqui você adicionaria autenticação
    return render_template('admin_dashboard.html')

@app.route("/api/admin/statistics")
def admin_statistics():
    """Estatísticas para o dashboard"""
    try:
        from database import db
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"💥 Error getting statistics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/alerts")
def admin_alerts():
    """Alertas não lidos"""
    try:
        from database import db
        alerts = db.get_unread_alerts()
        
        # Converter para formato JSON
        alerts_list = []
        for alert in alerts:
            alerts_list.append({
                'id': alert[0],
                'questionnaire_id': alert[1],
                'alert_type': alert[2],
                'message': alert[3],
                'is_read': alert[4],
                'created_at': alert[5],
                'questionnaire_type': alert[6],
                'total_score': alert[7],
                'first_name': alert[8],
                'last_name': alert[9],
                'completed_at': alert[10]
            })
        
        return jsonify(alerts_list)
    except Exception as e:
        print(f"💥 Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/alerts/<int:alert_id>/read", methods=['POST'])
def mark_alert_read(alert_id):
    """Marcar alerta como lido"""
    try:
        from database import db
        db.mark_alert_as_read(alert_id)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"💥 Error marking alert as read: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/results")
def admin_results():
    """Resultados de questionários"""
    try:
        from database import db
        results = db.get_all_results(limit=100)
        
        # Converter para formato JSON
        results_list = []
        for result in results:
            results_list.append({
                'id': result[0],
                'patient_id': result[1],
                'questionnaire_type': result[2],
                'answers': result[3],
                'total_score': result[4],
                'category': result[5],
                'interpretation': result[6],
                'completed_at': result[7],
                'token': result[8],
                'first_name': result[9],
                'last_name': result[10],
                'birth_date': result[11],
                'phone_number': result[12]
            })
        
        return jsonify(results_list)
    except Exception as e:
        print(f"💥 Error getting results: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/patient/<int:patient_id>/results")
def patient_results(patient_id):
    """Resultados de um paciente específico"""
    try:
        from database import db
        results = db.get_patient_results(patient_id)
        
        # Converter para formato JSON
        results_list = []
        for result in results:
            results_list.append({
                'id': result[0],
                'questionnaire_type': result[2],
                'total_score': result[4],
                'category': result[5],
                'completed_at': result[7],
                'answers': result[3]
            })
        
        return jsonify(results_list)
    except Exception as e:
        print(f"💥 Error getting patient results: {e}")
        return jsonify({"error": str(e)}), 500
'''

# Encontrar onde inserir (antes das outras rotas)
if '@app.route("/questionario/gad7/<token>")' in content:
    parts = content.split('@app.route("/questionario/gad7/<token>")')
    new_content = parts[0] + admin_routes + '\n\n@app.route("/questionario/gad7/<token>")' + parts[1]
else:
    # Se não encontrar, adicionar antes do if __name__
    if 'if __name__ == \'__main__\':' in content:
        parts = content.split('if __name__ == \'__main__\':')
        new_content = parts[0] + admin_routes + '\n\nif __name__ == \'__main__\':' + parts[1]
    else:
        new_content = content + '\n' + admin_routes

# Escrever arquivo atualizado
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'w') as f:
    f.write(new_content)

print("✅ Rotas administrativas adicionadas ao main.py")
