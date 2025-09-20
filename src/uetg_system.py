#!/usr/bin/env python3
"""
Sistema u-ETG para manejo de contingências
Sorteio automático de datas para exames de urina
"""
import sqlite3
import json
import random
from datetime import datetime, timedelta
import requests
import os

class UETGSystem:
    def __init__(self, db_path="medical_questionnaires.db"):
        self.db_path = db_path
        self.init_uetg_tables()
        
        # Configurações WhatsApp
        self.whatsapp_token = "EAANTZCXB0csgBPft9y6ZBIdeTVM5PVLr2ZBZAlTGd49ezcAklZCF4DDZC6r6NQ4nrDREkNnC6iEebI7YxciceIMF9BD9Cwp8OqVpBYxeZB2gAZADsVQZCsDbDZAlaPZC3iByj0ZAn2eaSrmjPaQPqZBX6UJZAK6Hd8MuXGoKVrLFPooE7so4G1w2wYNaxJYn1SgQ6RnwZDZD"
        self.phone_number_id = "797803706754193"
        self.admin_phone = "5514997799022"
    
    def init_uetg_tables(self):
        """Inicializar tabelas específicas do u-ETG"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de pacientes u-ETG
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uetg_patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                schedule_pattern TEXT NOT NULL,
                available_times TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sorteios semanais
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uetg_weekly_draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                week_start_date DATE NOT NULL,
                first_date DATE NOT NULL,
                second_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES uetg_patients (id)
            )
        ''')
        
        # Tabela de agendamentos confirmados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uetg_appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TEXT NOT NULL,
                status TEXT DEFAULT 'confirmed',
                draw_id INTEGER,
                confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES uetg_patients (id),
                FOREIGN KEY (draw_id) REFERENCES uetg_weekly_draws (id)
            )
        ''')
        
        # Tabela de mensagens enviadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uetg_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                message_type TEXT NOT NULL,
                message_content TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                draw_id INTEGER,
                FOREIGN KEY (patient_id) REFERENCES uetg_patients (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Tabelas u-ETG inicializadas!")
    
    def add_patient(self, name, phone_number, schedule_pattern="2x_week", available_times=None):
        """Adicionar paciente ao sistema u-ETG"""
        if available_times is None:
            available_times = ["12:15", "16:40", "19:00"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO uetg_patients (name, phone_number, schedule_pattern, available_times)
            VALUES (?, ?, ?, ?)
        ''', (name, phone_number, schedule_pattern, json.dumps(available_times)))
        
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Paciente {name} adicionado ao u-ETG (ID: {patient_id})")
        return patient_id
    
    def generate_weekly_draw(self, patient_id):
        """Gerar sorteio semanal para um paciente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar dados do paciente
        cursor.execute('SELECT * FROM uetg_patients WHERE id = ? AND is_active = 1', (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            print(f"❌ Paciente {patient_id} não encontrado ou inativo")
            return None
        
        # Debug: mostrar dados do paciente
        print(f"🔍 Dados do paciente: {patient}")
        print(f"🔍 Available times raw: {patient[4]}")
        
        # Tentar fazer parse do JSON
        try:
            available_times = json.loads(patient[4])
        except json.JSONDecodeError:
            # Se falhar, usar horários padrão
            available_times = ["12:15", "16:40", "19:00"]
            print(f"⚠️ Erro no JSON, usando horários padrão: {available_times}")
        
        # Calcular próxima semana (segunda-feira)
        today = datetime.now().date()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:  # Se hoje é segunda
            days_until_monday = 7
        
        next_monday = today + timedelta(days=days_until_monday)
        
        # Verificar se já existe sorteio para esta semana
        cursor.execute('''
            SELECT id FROM uetg_weekly_draws 
            WHERE patient_id = ? AND week_start_date = ?
        ''', (patient_id, next_monday))
        
        if cursor.fetchone():
            print(f"⚠️ Sorteio já existe para semana de {next_monday}")
            conn.close()
            return None
        
        # Sortear primeira data (segunda ou terça)
        first_options = [next_monday, next_monday + timedelta(days=1)]  # Seg, Ter
        first_date = random.choice(first_options)
        
        # Sortear segunda data (quinta ou sexta)
        second_options = [next_monday + timedelta(days=3), next_monday + timedelta(days=4)]  # Qui, Sex
        second_date = random.choice(second_options)
        
        # Salvar sorteio
        cursor.execute('''
            INSERT INTO uetg_weekly_draws (patient_id, week_start_date, first_date, second_date)
            VALUES (?, ?, ?, ?)
        ''', (patient_id, next_monday, first_date, second_date))
        
        draw_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        draw_info = {
            'draw_id': draw_id,
            'patient_name': patient[1],
            'patient_phone': patient[2],
            'first_date': first_date,
            'second_date': second_date,
            'available_times': available_times
        }
        
        print(f"🎲 Sorteio gerado para {patient[1]}: {first_date} e {second_date}")
        return draw_info
    
    def send_whatsapp_message(self, phone_number, message):
        """Enviar mensagem via WhatsApp"""
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                print(f"✅ Mensagem enviada para {phone_number}")
                return True
            else:
                print(f"❌ Erro ao enviar mensagem: {response.text}")
                return False
        except Exception as e:
            print(f"💥 Erro na API WhatsApp: {e}")
            return False
    
    def send_draw_notification_to_admin(self, draw_info):
        """Enviar notificação do sorteio para o admin"""
        first_date_str = draw_info['first_date'].strftime('%A %d/%m')
        second_date_str = draw_info['second_date'].strftime('%A %d/%m')
        
        # Traduzir dias da semana
        days_pt = {
            'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
            'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        
        for en, pt in days_pt.items():
            first_date_str = first_date_str.replace(en, pt)
            second_date_str = second_date_str.replace(en, pt)
        
        message = f"""🎲 SORTEIO u-ETG - {draw_info['patient_name']}

Datas sorteadas para esta semana:
• {first_date_str}
• {second_date_str}

As mensagens serão enviadas automaticamente às 07h de cada data sorteada."""
        
        success = self.send_whatsapp_message(self.admin_phone, message)
        
        if success:
            # Registrar mensagem enviada
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO uetg_messages (patient_id, message_type, message_content, draw_id)
                VALUES (?, ?, ?, ?)
            ''', (draw_info['draw_id'], 'admin_notification', message, draw_info['draw_id']))
            conn.commit()
            conn.close()
        
        return success
    
    def send_patient_draw_message(self, patient_phone, patient_name, available_times, date):
        """Enviar mensagem de sorteio para o paciente"""
        date_str = date.strftime('%A %d/%m')
        
        # Traduzir dia da semana
        days_pt = {
            'Monday': 'segunda', 'Tuesday': 'terça', 'Wednesday': 'quarta',
            'Thursday': 'quinta', 'Friday': 'sexta', 'Saturday': 'sábado', 'Sunday': 'domingo'
        }
        
        for en, pt in days_pt.items():
            date_str = date_str.replace(en, pt)
        
        times_list = '\n'.join([f"• {time}" for time in available_times])
        
        message = f"""Olá, {patient_name}, bom dia! Tudo bem? 😄

Você foi "sorteado" hoje! Conforme combinamos, preciso que você faça o u-ETG (exame de urina) hoje no consultório comigo.

Horários disponíveis:
{times_list}

Me diga qual você prefere respondendo com o horário (ex.: "16:40") e já deixamos combinado! Um ótimo dia!"""
        
        return self.send_whatsapp_message(patient_phone, message)
    
    def process_patient_time_selection(self, patient_phone, selected_time, date):
        """Processar seleção de horário do paciente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar paciente pelo telefone
        cursor.execute('SELECT * FROM uetg_patients WHERE phone_number = ?', (patient_phone,))
        patient = cursor.fetchone()
        
        if not patient:
            conn.close()
            return False
        
        patient_id = patient[0]
        patient_name = patient[1]
        
        # Buscar sorteio ativo para esta data
        cursor.execute('''
            SELECT id FROM uetg_weekly_draws 
            WHERE patient_id = ? AND (first_date = ? OR second_date = ?)
            ORDER BY created_at DESC LIMIT 1
        ''', (patient_id, date, date))
        
        draw = cursor.fetchone()
        draw_id = draw[0] if draw else None
        
        # Salvar agendamento
        cursor.execute('''
            INSERT INTO uetg_appointments (patient_id, appointment_date, appointment_time, draw_id)
            VALUES (?, ?, ?, ?)
        ''', (patient_id, date, selected_time, draw_id))
        
        conn.commit()
        conn.close()
        
        # Enviar confirmação para o paciente
        date_str = date.strftime('%A %d/%m')
        days_pt = {
            'Monday': 'segunda', 'Tuesday': 'terça', 'Wednesday': 'quarta',
            'Thursday': 'quinta', 'Friday': 'sexta', 'Saturday': 'sábado', 'Sunday': 'domingo'
        }
        
        for en, pt in days_pt.items():
            date_str = date_str.replace(en, pt)
        
        confirmation_msg = f"Perfeito! {date_str} às {selected_time}. Te espero! 👍"
        self.send_whatsapp_message(patient_phone, confirmation_msg)
        
        # Notificar admin
        admin_msg = f"✅ {patient_name} confirmou: {date_str} às {selected_time}"
        self.send_whatsapp_message(self.admin_phone, admin_msg)
        
        print(f"✅ Agendamento confirmado: {patient_name} - {date} às {selected_time}")
        return True
    
    def get_weekly_schedule(self, week_start_date=None):
        """Obter agenda da semana"""
        if week_start_date is None:
            today = datetime.now().date()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            week_start_date = today + timedelta(days=days_until_monday)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.*, p.name, p.phone_number,
                   a1.appointment_time as first_time,
                   a2.appointment_time as second_time
            FROM uetg_weekly_draws d
            JOIN uetg_patients p ON d.patient_id = p.id
            LEFT JOIN uetg_appointments a1 ON d.id = a1.draw_id AND d.first_date = a1.appointment_date
            LEFT JOIN uetg_appointments a2 ON d.id = a2.draw_id AND d.second_date = a2.appointment_date
            WHERE d.week_start_date = ?
            ORDER BY d.created_at
        ''', (week_start_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

# Instância global
uetg = UETGSystem()

if __name__ == "__main__":
    # Teste do sistema
    print("🧪 Testando sistema u-ETG...")
    
    # Adicionar Filipe
    patient_id = uetg.add_patient("Filipe", "5514999999999")  # Número de teste
    
    # Gerar sorteio
    draw_info = uetg.generate_weekly_draw(patient_id)
    
    if draw_info:
        print(f"📊 Sorteio: {draw_info}")
        
        # Simular notificação admin
        uetg.send_draw_notification_to_admin(draw_info)
        
        # Simular mensagem para paciente (primeira data)
        uetg.send_patient_draw_message(
            draw_info['patient_phone'],
            draw_info['patient_name'],
            draw_info['available_times'],
            draw_info['first_date']
        )
    
    print("✅ Teste concluído!")
