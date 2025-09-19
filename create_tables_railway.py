#!/usr/bin/env python3
"""
Script para criar tabelas no banco de dados do Railway
"""

import requests
import json
from datetime import datetime

# Configurações
RAILWAY_URL = "https://web-production-4fc41.up.railway.app"
ADMIN_TOKEN = "admin123456"

def create_tables():
    """Força criação das tabelas via endpoint"""
    print("🗄️ CRIANDO TABELAS NO BANCO DE DADOS")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🌐 URL: {RAILWAY_URL}")
    print("=" * 60)
    
    try:
        # Headers com token admin
        headers = {
            "Content-Type": "application/json",
            "X-Admin-Token": ADMIN_TOKEN
        }
        
        print(f"📤 Enviando requisição para criar tabelas...")
        
        # Tenta criar tabelas via endpoint
        response = requests.post(
            f"{RAILWAY_URL}/admin/api/create-tables",
            headers=headers,
            timeout=30
        )
        
        print(f"\n📊 RESULTADO:")
        print(f"🌐 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tabelas criadas com sucesso!")
            print(f"📋 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Erro ao criar tabelas: {response.status_code}")
            print(f"📄 Response Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_patient_after_tables():
    """Testa registro de paciente após criar tabelas"""
    print("\n👤 TESTE DE REGISTRO APÓS CRIAÇÃO DE TABELAS")
    print("=" * 60)
    
    try:
        # Dados do paciente
        patient_data = {
            "name": "Guilherme Bueno",
            "phone": "(14) 99779-9022",
            "email": "guilherme@exemplo.com",
            "birth_date": "1990-01-01",
            "gender": "M",
            "protocols": {
                "uetg": {
                    "enabled": True,
                    "frequency": "random",
                    "time": "07:30"
                },
                "gad7": {
                    "enabled": True,
                    "frequency": "weekly",
                    "time": "09:00"
                },
                "phq9": {
                    "enabled": True,
                    "frequency": "weekly", 
                    "time": "10:00"
                },
                "asrs18": {
                    "enabled": True,
                    "frequency": "monthly",
                    "time": "11:00"
                }
            },
            "priority": "normal",
            "notes": "Paciente de teste para sistema u-ETG e escalas psicológicas",
            "active": True
        }
        
        # Headers com token admin
        headers = {
            "Content-Type": "application/json",
            "X-Admin-Token": ADMIN_TOKEN
        }
        
        print(f"📤 Registrando paciente Guilherme Bueno...")
        
        # Registra paciente
        response = requests.post(
            f"{RAILWAY_URL}/admin/api/patients",
            json=patient_data,
            headers=headers,
            timeout=30
        )
        
        print(f"🌐 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Paciente registrado com sucesso!")
            print(f"👤 ID: {result.get('patient', {}).get('id')}")
            print(f"📱 Telefone: {result.get('patient', {}).get('phone_masked')}")
            return result.get('patient', {}).get('id')
        else:
            print(f"❌ Erro ao registrar paciente: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def main():
    """Função principal"""
    print("🚀 CRIAÇÃO DE TABELAS E TESTE DE PACIENTE")
    print("=" * 80)
    
    # 1. Criar tabelas
    tables_created = create_tables()
    
    # 2. Testar registro de paciente
    patient_id = None
    if tables_created:
        print("\n⏳ Aguardando 5 segundos para estabilizar...")
        import time
        time.sleep(5)
        patient_id = test_patient_after_tables()
    
    # 3. Resumo dos resultados
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS RESULTADOS")
    print("=" * 80)
    
    print(f"{'✅' if tables_created else '❌'} Criação de Tabelas: {'OK' if tables_created else 'FALHOU'}")
    print(f"{'✅' if patient_id else '❌'} Registro Paciente: {'OK' if patient_id else 'FALHOU'}")
    
    if patient_id:
        print(f"\n🎉 SUCESSO COMPLETO!")
        print(f"👤 Paciente Guilherme Bueno registrado com ID: {patient_id}")
        print(f"📱 Telefone: (14) 99779-9022")
        print(f"🔄 Todos os protocolos habilitados: u-ETG, GAD-7, PHQ-9, ASRS-18")
    else:
        print(f"\n❌ FALHA!")
        if not tables_created:
            print(f"🗄️ Não foi possível criar as tabelas do banco de dados")
        else:
            print(f"👤 Não foi possível registrar o paciente")
    
    print(f"\n🔗 PRÓXIMOS PASSOS:")
    if patient_id:
        print(f"1. Verificar lista de pacientes no painel admin")
        print(f"2. Testar envio de templates WhatsApp")
        print(f"3. Configurar templates no Facebook Business Manager")
    else:
        print(f"1. Verificar logs do Railway para erros detalhados")
        print(f"2. Executar script de criação de tabelas localmente")
        print(f"3. Verificar configuração do banco SQLite")
    
    print(f"\n🔗 LINKS ÚTEIS:")
    print(f"• Painel Admin: {RAILWAY_URL}/admin")
    print(f"• Lista Pacientes: {RAILWAY_URL}/admin/patients")
    print(f"• Health Check: {RAILWAY_URL}/health")
    
    return patient_id is not None

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
