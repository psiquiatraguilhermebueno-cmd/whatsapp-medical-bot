#!/usr/bin/env python3
"""
Script para testar API de registro de pacientes diretamente
"""

import requests
import json
from datetime import datetime

# Configurações
RAILWAY_URL = "https://web-production-4fc41.up.railway.app"
ADMIN_TOKEN = "admin123456"

def test_patient_registration():
    """Testa registro de paciente via API"""
    print("🧪 TESTE DE REGISTRO DE PACIENTE VIA API")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🌐 URL: {RAILWAY_URL}")
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
        
        print(f"📤 Enviando dados do paciente...")
        print(f"📋 Payload: {json.dumps(patient_data, indent=2, ensure_ascii=False)}")
        print(f"🔑 Headers: {headers}")
        
        # Registra paciente
        response = requests.post(
            f"{RAILWAY_URL}/admin/api/patients",
            json=patient_data,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📊 RESULTADO:")
        print(f"🌐 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Paciente registrado com sucesso!")
            print(f"📋 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result.get('patient', {}).get('id')
        else:
            print(f"❌ Erro ao registrar paciente: {response.status_code}")
            print(f"📄 Response Text: {response.text}")
            
            # Tenta decodificar JSON se possível
            try:
                error_json = response.json()
                print(f"📋 Error JSON: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
            except:
                print("❌ Resposta não é JSON válido")
            
            return None
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout na requisição (30s)")
        return None
    except requests.exceptions.ConnectionError:
        print(f"🌐 Erro de conexão")
        return None
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def test_health_check():
    """Testa health check da aplicação"""
    print("\n🏥 TESTE DE HEALTH CHECK")
    print("=" * 60)
    
    try:
        response = requests.get(f"{RAILWAY_URL}/health", timeout=10)
        
        print(f"🌐 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check OK!")
            print(f"📋 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Health check falhou: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

def test_admin_endpoint():
    """Testa endpoint admin"""
    print("\n🔐 TESTE DE ENDPOINT ADMIN")
    print("=" * 60)
    
    try:
        response = requests.get(f"{RAILWAY_URL}/admin", timeout=10)
        
        print(f"🌐 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Endpoint admin acessível!")
            print(f"📄 Content-Type: {response.headers.get('content-type', 'N/A')}")
            return True
        else:
            print(f"❌ Endpoint admin falhou: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erro no endpoint admin: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO DA API DE PACIENTES")
    print("=" * 80)
    
    # 1. Teste health check
    health_ok = test_health_check()
    
    # 2. Teste endpoint admin
    admin_ok = test_admin_endpoint()
    
    # 3. Teste registro de paciente
    patient_id = test_patient_registration()
    
    # 4. Resumo dos resultados
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    print(f"{'✅' if health_ok else '❌'} Health Check: {'OK' if health_ok else 'FALHOU'}")
    print(f"{'✅' if admin_ok else '❌'} Endpoint Admin: {'OK' if admin_ok else 'FALHOU'}")
    print(f"{'✅' if patient_id else '❌'} Registro Paciente: {'OK' if patient_id else 'FALHOU'}")
    
    if patient_id:
        print(f"\n🎉 SUCESSO! Paciente registrado com ID: {patient_id}")
    else:
        print(f"\n❌ FALHA! Não foi possível registrar o paciente")
        print(f"\n🔧 POSSÍVEIS CAUSAS:")
        print(f"1. Erro na rota /admin/api/patients")
        print(f"2. Problema de autenticação com token admin")
        print(f"3. Erro no banco de dados SQLAlchemy")
        print(f"4. Problema na validação dos dados")
        print(f"5. Erro interno do servidor (500)")
    
    print(f"\n🔗 LINKS ÚTEIS:")
    print(f"• Health Check: {RAILWAY_URL}/health")
    print(f"• Painel Admin: {RAILWAY_URL}/admin")
    print(f"• Formulário Pacientes: {RAILWAY_URL}/admin/patients/new")
    
    return patient_id is not None

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
