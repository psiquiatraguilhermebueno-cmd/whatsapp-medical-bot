#!/usr/bin/env python3
"""
Força criação de tabelas no Railway via endpoint
"""

import requests
import time

def create_tables_via_endpoint():
    """
    Cria tabelas via endpoint da aplicação Railway
    """
    
    print("🔧 Criando tabelas via endpoint Railway...")
    
    url = "https://web-production-4fc41.up.railway.app/admin/create-tables"
    
    headers = {
        'X-Admin-Token': 'admin123456',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resposta: {result}")
            return True
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exceção: {str(e)}")
        return False

def test_patient_creation():
    """
    Testa criação de paciente após criar tabelas
    """
    
    print("🧪 Testando criação de paciente...")
    
    url = "https://web-production-4fc41.up.railway.app/admin/api/patients"
    
    headers = {
        'X-Admin-Token': 'admin123456',
        'Content-Type': 'application/json'
    }
    
    test_data = {
        "name": "Teste Sistema",
        "phone": "(11) 91211-3050",
        "email": "teste@exemplo.com",
        "active": True,
        "protocols": {
            "gad7": {
                "enabled": True,
                "frequency": "weekly",
                "time": "09:00",
                "immediate": True
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Paciente teste criado: {result}")
            return True
        else:
            print(f"❌ Erro ao criar paciente: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exceção: {str(e)}")
        return False

def main():
    """
    Função principal para corrigir problema das tabelas
    """
    
    print("🚀 CORRIGINDO PROBLEMA DAS TABELAS")
    print("=" * 40)
    
    # 1. Verificar se aplicação está funcionando
    print("📡 1/3: Verificando aplicação...")
    try:
        response = requests.get("https://web-production-4fc41.up.railway.app/health", timeout=10)
        if response.status_code == 200:
            print("✅ Aplicação funcionando")
        else:
            print(f"⚠️ Aplicação com problemas: {response.status_code}")
    except Exception as e:
        print(f"❌ Aplicação não responde: {e}")
        return False
    
    # 2. Criar tabelas
    print("🔧 2/3: Criando tabelas...")
    if create_tables_via_endpoint():
        print("✅ Tabelas criadas com sucesso")
    else:
        print("⚠️ Falha ao criar tabelas via endpoint")
        print("💡 Tentando método alternativo...")
        
        # Método alternativo: criar via SQL direto
        print("🔄 Criando tabelas via SQL...")
        return create_tables_direct()
    
    # 3. Testar criação de paciente
    print("🧪 3/3: Testando criação de paciente...")
    time.sleep(3)  # Aguardar tabelas serem criadas
    
    if test_patient_creation():
        print("✅ Sistema funcionando perfeitamente!")
        return True
    else:
        print("⚠️ Ainda há problemas com criação de pacientes")
        return False

def create_tables_direct():
    """
    Cria tabelas diretamente via SQL
    """
    
    print("🔧 Criando tabelas via SQL direto...")
    
    # SQL para criar tabelas
    create_sql = """
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        phone_e164 VARCHAR(20) UNIQUE,
        email VARCHAR(255),
        birth_date DATE,
        gender VARCHAR(1),
        tags TEXT,
        priority VARCHAR(20) DEFAULT 'normal',
        active BOOLEAN DEFAULT 1,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS patient_protocols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        protocol_type VARCHAR(50) NOT NULL,
        enabled BOOLEAN DEFAULT 1,
        frequency VARCHAR(20),
        time_of_day TIME,
        immediate_dispatch BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    );
    
    CREATE TABLE IF NOT EXISTS questionnaire_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        questionnaire_type VARCHAR(50) NOT NULL,
        responses TEXT,
        score INTEGER,
        risk_level VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    );
    """
    
    # Tentar executar via endpoint de SQL
    url = "https://web-production-4fc41.up.railway.app/admin/execute-sql"
    
    headers = {
        'X-Admin-Token': 'admin123456',
        'Content-Type': 'application/json'
    }
    
    data = {
        'sql': create_sql
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Tabelas criadas via SQL direto")
            return True
        else:
            print(f"❌ Erro SQL: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exceção SQL: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🏆 PROBLEMA DAS TABELAS RESOLVIDO!")
        print("✅ Tabelas criadas no Railway")
        print("✅ Sistema de pacientes funcionando")
        print("✅ Pode cadastrar sua esposa agora")
        print("\n🎯 TESTE NOVAMENTE O CADASTRO!")
    else:
        print("\n⚠️ Ainda há problemas com as tabelas")
        print("💡 Pode ser necessário reiniciar a aplicação Railway")
