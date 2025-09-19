#!/usr/bin/env python3
"""
Sistema de banco de dados para questionários médicos
"""
import sqlite3
import json
from datetime import datetime
import os

class MedicalDatabase:
    def __init__(self, db_path="medical_questionnaires.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar banco de dados com tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de pacientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birth_date DATE NOT NULL,
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(first_name, last_name, birth_date)
            )
        ''')
        
        # Tabela de questionários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questionnaires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                questionnaire_type TEXT NOT NULL,
                answers TEXT NOT NULL,
                total_score INTEGER NOT NULL,
                category TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                token TEXT UNIQUE,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Tabela de agendamentos automáticos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_questionnaires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                questionnaire_type TEXT NOT NULL,
                frequency_days INTEGER NOT NULL,
                last_sent TIMESTAMP,
                next_due TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Tabela de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                questionnaire_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (questionnaire_id) REFERENCES questionnaires (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    
    def add_patient(self, first_name, last_name, birth_date, phone_number=None):
        """Adicionar ou buscar paciente existente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Tentar inserir novo paciente
            cursor.execute('''
                INSERT INTO patients (first_name, last_name, birth_date, phone_number)
                VALUES (?, ?, ?, ?)
            ''', (first_name, last_name, birth_date, phone_number))
            patient_id = cursor.lastrowid
            print(f"✅ Novo paciente criado: {first_name} {last_name} (ID: {patient_id})")
            
        except sqlite3.IntegrityError:
            # Paciente já existe, buscar ID
            cursor.execute('''
                SELECT id FROM patients 
                WHERE first_name = ? AND last_name = ? AND birth_date = ?
            ''', (first_name, last_name, birth_date))
            patient_id = cursor.fetchone()[0]
            print(f"✅ Paciente existente encontrado: {first_name} {last_name} (ID: {patient_id})")
        
        conn.commit()
        conn.close()
        return patient_id
    
    def save_questionnaire_result(self, patient_data, questionnaire_type, answers, total_score, category, interpretation, token=None):
        """Salvar resultado de questionário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Adicionar/buscar paciente
        patient_id = self.add_patient(
            patient_data['firstName'],
            patient_data['lastName'], 
            patient_data['birthDate'],
            patient_data.get('phone')
        )
        
        # Salvar questionário
        cursor.execute('''
            INSERT INTO questionnaires 
            (patient_id, questionnaire_type, answers, total_score, category, interpretation, token)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, questionnaire_type, json.dumps(answers), total_score, category, interpretation, token))
        
        questionnaire_id = cursor.lastrowid
        
        # Verificar se precisa criar alerta
        self._check_and_create_alert(cursor, questionnaire_id, questionnaire_type, total_score, patient_data)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Questionário {questionnaire_type} salvo para {patient_data['firstName']} {patient_data['lastName']}")
        print(f"📊 Pontuação: {total_score} - {category}")
        
        return questionnaire_id
    
    def _check_and_create_alert(self, cursor, questionnaire_id, questionnaire_type, total_score, patient_data):
        """Verificar se precisa criar alerta para casos severos"""
        alert_needed = False
        alert_message = ""
        
        if questionnaire_type == "GAD-7" and total_score >= 15:
            alert_needed = True
            alert_message = f"🚨 ALERTA: {patient_data['firstName']} {patient_data['lastName']} apresentou ansiedade severa (GAD-7: {total_score}/21)"
        
        elif questionnaire_type == "PHQ-9" and total_score >= 20:
            alert_needed = True
            alert_message = f"🚨 ALERTA: {patient_data['firstName']} {patient_data['lastName']} apresentou depressão severa (PHQ-9: {total_score}/27)"
        
        if alert_needed:
            cursor.execute('''
                INSERT INTO alerts (questionnaire_id, alert_type, message)
                VALUES (?, ?, ?)
            ''', (questionnaire_id, "SEVERE_SCORE", alert_message))
            print(f"🚨 ALERTA CRIADO: {alert_message}")
    
    def get_patient_results(self, patient_id, questionnaire_type=None):
        """Buscar resultados de um paciente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT q.*, p.first_name, p.last_name, p.birth_date
            FROM questionnaires q
            JOIN patients p ON q.patient_id = p.id
            WHERE q.patient_id = ?
        '''
        params = [patient_id]
        
        if questionnaire_type:
            query += ' AND q.questionnaire_type = ?'
            params.append(questionnaire_type)
        
        query += ' ORDER BY q.completed_at DESC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_all_results(self, limit=100):
        """Buscar todos os resultados recentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT q.*, p.first_name, p.last_name, p.birth_date, p.phone_number
            FROM questionnaires q
            JOIN patients p ON q.patient_id = p.id
            ORDER BY q.completed_at DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_unread_alerts(self):
        """Buscar alertas não lidos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, q.questionnaire_type, q.total_score, 
                   p.first_name, p.last_name, q.completed_at
            FROM alerts a
            JOIN questionnaires q ON a.questionnaire_id = q.id
            JOIN patients p ON q.patient_id = p.id
            WHERE a.is_read = 0
            ORDER BY a.created_at DESC
        ''')
        
        alerts = cursor.fetchall()
        conn.close()
        
        return alerts
    
    def mark_alert_as_read(self, alert_id):
        """Marcar alerta como lido"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE alerts SET is_read = 1 WHERE id = ?', (alert_id,))
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """Obter estatísticas gerais"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de pacientes
        cursor.execute('SELECT COUNT(*) FROM patients')
        stats['total_patients'] = cursor.fetchone()[0]
        
        # Total de questionários
        cursor.execute('SELECT COUNT(*) FROM questionnaires')
        stats['total_questionnaires'] = cursor.fetchone()[0]
        
        # Questionários por tipo
        cursor.execute('''
            SELECT questionnaire_type, COUNT(*) 
            FROM questionnaires 
            GROUP BY questionnaire_type
        ''')
        stats['by_type'] = dict(cursor.fetchall())
        
        # Alertas não lidos
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_read = 0')
        stats['unread_alerts'] = cursor.fetchone()[0]
        
        # Questionários hoje
        cursor.execute('''
            SELECT COUNT(*) FROM questionnaires 
            WHERE DATE(completed_at) = DATE('now')
        ''')
        stats['today_questionnaires'] = cursor.fetchone()[0]
        
        # Casos severos (últimos 30 dias)
        cursor.execute('''
            SELECT COUNT(*) FROM questionnaires 
            WHERE (questionnaire_type = 'GAD-7' AND total_score >= 15)
               OR (questionnaire_type = 'PHQ-9' AND total_score >= 20)
            AND completed_at >= datetime('now', '-30 days')
        ''')
        stats['severe_cases_30d'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

# Instância global do banco
db = MedicalDatabase()

if __name__ == "__main__":
    # Teste do banco de dados
    print("🧪 Testando banco de dados...")
    
    # Teste de paciente
    patient_id = db.add_patient("João", "Silva", "1990-01-01", "11999999999")
    
    # Teste de questionário
    patient_data = {
        'firstName': 'João',
        'lastName': 'Silva', 
        'birthDate': '1990-01-01'
    }
    
    answers = [1, 2, 0, 3, 1, 2, 1]
    total_score = sum(answers)
    
    questionnaire_id = db.save_questionnaire_result(
        patient_data, "GAD-7", answers, total_score, "Ansiedade Moderada", 
        "Sintomas moderados de ansiedade.", "test-token-123"
    )
    
    # Teste de estatísticas
    stats = db.get_statistics()
    print(f"📊 Estatísticas: {stats}")
    
    print("✅ Teste concluído!")
