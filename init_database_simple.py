#!/usr/bin/env python3
"""
Script simples para inicializar banco de dados
"""

import os
import sys
import sqlite3
from datetime import datetime

def create_database_tables():
    """Cria tabelas SQLite diretamente"""
    print("🗄️ CRIANDO TABELAS SQLITE DIRETAMENTE")
    print("=" * 60)
    
    # Caminho do banco de dados
    db_path = "instance/medical_bot.db"
    
    # Criar diretório instance se não existir
    os.makedirs("instance", exist_ok=True)
    
    try:
        # Conectar ao banco SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📁 Banco de dados: {db_path}")
        
        # Criar tabela patients
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            phone_e164 VARCHAR(20) UNIQUE NOT NULL,
            phone_masked VARCHAR(20),
            email VARCHAR(255),
            birth_date DATE,
            gender CHAR(1),
            tags TEXT,
            priority VARCHAR(20) DEFAULT 'normal',
            notes TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("✅ Tabela 'patients' criada")
        
        # Criar tabela responses
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            questionnaire_type VARCHAR(50) NOT NULL,
            question_number INTEGER NOT NULL,
            response_value INTEGER NOT NULL,
            response_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
        ''')
        print("✅ Tabela 'responses' criada")
        
        # Criar tabela schedules
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            protocol_type VARCHAR(50) NOT NULL,
            frequency VARCHAR(20) NOT NULL,
            time VARCHAR(10) NOT NULL,
            days_of_week TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
        ''')
        print("✅ Tabela 'schedules' criada")
        
        # Commit e fechar
        conn.commit()
        conn.close()
        
        print(f"\n✅ BANCO DE DADOS INICIALIZADO COM SUCESSO!")
        print(f"📁 Localização: {os.path.abspath(db_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def test_patient_registration_local():
    """Testa registro de paciente localmente"""
    print("\n👤 TESTE DE REGISTRO LOCAL")
    print("=" * 60)
    
    db_path = "instance/medical_bot.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Inserir paciente de teste
        cursor.execute('''
        INSERT OR REPLACE INTO patients 
        (name, phone_e164, phone_masked, email, birth_date, gender, priority, notes, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Guilherme Bueno',
            '5514997799022',
            '(14) 99779-9022',
            'guilherme@exemplo.com',
            '1990-01-01',
            'M',
            'normal',
            'Paciente de teste para sistema u-ETG e escalas psicológicas',
            1
        ))
        
        patient_id = cursor.lastrowid
        
        # Inserir agendamentos
        protocols = [
            ('uetg', 'random', '07:30'),
            ('gad7', 'weekly', '09:00'),
            ('phq9', 'weekly', '10:00'),
            ('asrs18', 'monthly', '11:00')
        ]
        
        for protocol, frequency, time in protocols:
            cursor.execute('''
            INSERT INTO schedules (patient_id, protocol_type, frequency, time, active)
            VALUES (?, ?, ?, ?, ?)
            ''', (patient_id, protocol, frequency, time, 1))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Paciente registrado localmente!")
        print(f"👤 ID: {patient_id}")
        print(f"📱 Telefone: (14) 99779-9022")
        print(f"🔄 Protocolos: u-ETG, GAD-7, PHQ-9, ASRS-18")
        
        return patient_id
        
    except Exception as e:
        print(f"❌ Erro ao registrar paciente: {e}")
        return None

def upload_database_to_railway():
    """Faz upload do banco local para o Railway"""
    print("\n☁️ UPLOAD DO BANCO PARA RAILWAY")
    print("=" * 60)
    
    # Este seria um processo mais complexo
    # Por enquanto, vamos apenas mostrar as instruções
    print("📋 INSTRUÇÕES PARA UPLOAD:")
    print("1. O banco SQLite foi criado localmente em instance/medical_bot.db")
    print("2. O Railway deve usar este mesmo esquema de tabelas")
    print("3. As tabelas serão criadas automaticamente quando a aplicação iniciar")
    print("4. O endpoint /admin/api/patients deve funcionar agora")
    
    return True

def main():
    """Função principal"""
    print("🚀 INICIALIZAÇÃO COMPLETA DO BANCO DE DADOS")
    print("=" * 80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    # 1. Criar tabelas
    tables_created = create_database_tables()
    
    # 2. Testar registro local
    patient_id = None
    if tables_created:
        patient_id = test_patient_registration_local()
    
    # 3. Instruções para Railway
    if patient_id:
        upload_database_to_railway()
    
    # 4. Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO FINAL")
    print("=" * 80)
    
    print(f"{'✅' if tables_created else '❌'} Criação de Tabelas: {'OK' if tables_created else 'FALHOU'}")
    print(f"{'✅' if patient_id else '❌'} Registro Local: {'OK' if patient_id else 'FALHOU'}")
    
    if patient_id:
        print(f"\n🎉 SUCESSO TOTAL!")
        print(f"📁 Banco criado: instance/medical_bot.db")
        print(f"👤 Paciente registrado: Guilherme Bueno (ID: {patient_id})")
        print(f"🔄 Protocolos configurados: u-ETG, GAD-7, PHQ-9, ASRS-18")
        
        print(f"\n🚀 PRÓXIMOS PASSOS:")
        print(f"1. Testar formulário web no Railway")
        print(f"2. Verificar se as tabelas existem na aplicação")
        print(f"3. Registrar paciente via interface web")
        print(f"4. Configurar templates WhatsApp")
    else:
        print(f"\n❌ FALHA!")
        print(f"Não foi possível inicializar o banco de dados")
    
    return patient_id is not None

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
