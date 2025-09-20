#!/usr/bin/env python3
"""
Implementar automação real do u-ETG para produção
"""
import os
import sys

# Adicionar sistema de agendamento automático
automation_code = '''
# ==================== AUTOMAÇÃO u-ETG ====================

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

# Inicializar scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Registrar shutdown
atexit.register(lambda: scheduler.shutdown())

def weekly_uetg_draw():
    """Sorteio automático semanal - Domingos às 20h"""
    try:
        from uetg_system import uetg
        import sqlite3
        from datetime import datetime, timedelta
        
        print("🎲 Executando sorteio automático semanal...")
        
        # Buscar todos os pacientes ativos
        conn = sqlite3.connect(uetg.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM uetg_patients WHERE is_active = 1')
        patients = cursor.fetchall()
        conn.close()
        
        for patient in patients:
            patient_id = patient[0]
            patient_name = patient[1]
            patient_phone = patient[2]
            
            print(f"📋 Gerando sorteio para {patient_name}")
            
            # Gerar sorteio
            success = uetg.generate_weekly_draw(patient_id)
            
            if success:
                # Buscar datas sorteadas
                conn = sqlite3.connect(uetg.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT first_date, second_date FROM uetg_weekly_draws 
                    WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1
                """, (patient_id,))
                draw = cursor.fetchone()
                conn.close()
                
                if draw:
                    first_date = draw[0]
                    second_date = draw[1]
                    
                    # Notificar admin
                    admin_message = f"""🎲 SORTEIO u-ETG - {patient_name}

Datas sorteadas para esta semana:
• {first_date}
• {second_date}

As mensagens serão enviadas automaticamente às 07h de cada data sorteada."""
                    
                    send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)
                    print(f"✅ Sorteio gerado e admin notificado para {patient_name}")
                
    except Exception as e:
        print(f"💥 Erro no sorteio automático: {e}")
        # Notificar admin sobre erro
        send_whatsapp_message(ADMIN_PHONE_NUMBER, f"❌ Erro no sorteio automático: {e}")

def daily_uetg_check():
    """Verificação diária - Enviar mensagens às 07h se data sorteada"""
    try:
        from uetg_system import uetg
        import sqlite3
        from datetime import datetime
        import json
        
        today = datetime.now().date()
        print(f"🔍 Verificando envios u-ETG para {today}")
        
        # Buscar sorteios para hoje
        conn = sqlite3.connect(uetg.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, p.name, p.phone_number, p.available_times 
            FROM uetg_weekly_draws d
            JOIN uetg_patients p ON d.patient_id = p.id
            WHERE (d.first_date = ? OR d.second_date = ?) AND p.is_active = 1
        """, (today, today))
        
        draws_today = cursor.fetchall()
        conn.close()
        
        for draw in draws_today:
            patient_name = draw[5]
            patient_phone = draw[6]
            available_times_str = draw[7]
            
            try:
                available_times = json.loads(available_times_str)
            except:
                available_times = ["12:15", "16:40", "19:00"]
            
            print(f"📤 Enviando mensagem u-ETG para {patient_name}")
            
            # Enviar mensagem u-ETG
            success = uetg.send_patient_draw_message(patient_phone, patient_name, available_times, today)
            
            if success:
                print(f"✅ Mensagem enviada para {patient_name}")
                
                # Notificar admin
                admin_message = f"📤 Mensagem u-ETG enviada para {patient_name} - {today}"
                send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)
            else:
                print(f"❌ Falha ao enviar para {patient_name}")
                send_whatsapp_message(ADMIN_PHONE_NUMBER, f"❌ Falha no envio u-ETG para {patient_name}")
                
    except Exception as e:
        print(f"💥 Erro na verificação diária: {e}")
        send_whatsapp_message(ADMIN_PHONE_NUMBER, f"❌ Erro na verificação diária u-ETG: {e}")

# Agendar tarefas
# Sorteio semanal: Domingos às 20h
scheduler.add_job(
    func=weekly_uetg_draw,
    trigger=CronTrigger(day_of_week=6, hour=20, minute=0),  # Domingo = 6
    id='weekly_uetg_draw',
    name='Sorteio Semanal u-ETG',
    replace_existing=True
)

# Verificação diária: Todos os dias às 07h
scheduler.add_job(
    func=daily_uetg_check,
    trigger=CronTrigger(hour=7, minute=0),
    id='daily_uetg_check',
    name='Verificação Diária u-ETG',
    replace_existing=True
)

print("⏰ Automação u-ETG configurada:")
print("   - Sorteio semanal: Domingos às 20h")
print("   - Envio automático: Diariamente às 07h (se data sorteada)")
'''

# Ler arquivo main.py atual
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'r') as f:
    content = f.read()

# Adicionar automação antes da última linha
lines = content.split('\n')
insert_position = -5  # Antes do final

# Inserir código de automação
lines.insert(insert_position, automation_code)

# Escrever arquivo atualizado
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'w') as f:
    f.write('\n'.join(lines))

print("✅ Automação u-ETG adicionada ao main.py")

# Adicionar dependência APScheduler ao requirements.txt
requirements_content = """flask
requests
apscheduler
"""

with open('/home/ubuntu/whatsapp-medical-bot/requirements.txt', 'w') as f:
    f.write(requirements_content)

print("✅ Dependências atualizadas")

# Cadastrar Filipe no sistema
filipe_data = {
    "name": "Filipe",
    "phone_number": "5514997799022",  # Número do Filipe (ajustar conforme necessário)
    "available_times": ["12:15", "16:40", "19:00"],
    "is_active": True
}

print("✅ Dados do Filipe preparados para cadastro")
print(f"   Nome: {filipe_data['name']}")
print(f"   Telefone: {filipe_data['phone_number']}")
print(f"   Horários: {filipe_data['available_times']}")

print("\n🎯 PRÓXIMOS PASSOS:")
print("1. Deploy da automação")
print("2. Cadastrar Filipe via interface")
print("3. Gerar primeiro sorteio")
print("4. Testar funcionamento")
