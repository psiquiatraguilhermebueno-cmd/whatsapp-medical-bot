#!/usr/bin/env python3
import requests
import json

def test_patient():
    url = "https://web-production-4fc41.up.railway.app/admin/api/patients/simple"
    
    data = {
        "name": "Guilherme Bueno",
        "phone": "(14) 99779-9022",
        "email": "guilherme@exemplo.com",
        "birth_date": "1990-01-01",
        "gender": "M",
        "notes": "Paciente teste - sistema completo"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Token": "admin123456"
    }
    
    print("🧪 Testando endpoint simplificado...")
    print(f"📤 URL: {url}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ SUCESSO!")
            print(f"📋 {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ ERRO: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    success = test_patient()
    print(f"\n{'✅ TESTE PASSOU' if success else '❌ TESTE FALHOU'}")
