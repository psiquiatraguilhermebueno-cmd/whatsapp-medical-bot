#!/usr/bin/env python3
"""
Correção simples e direta do banco de dados
"""

import os

def add_simple_patient_endpoint():
    """Adiciona endpoint simplificado para pacientes"""
    
    print("👤 Adicionando endpoint simplificado...")
    
    # Lê o main.py atual
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Endpoint simplificado
    simple_endpoint = '''
@app.route('/admin/api/patients/simple', methods=['POST'])
def create_patient_simple():
    """Endpoint simplificado para criar paciente"""
    try:
        # Verifica token admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin123456':
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Obter dados
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not name or not phone:
            return jsonify({'error': 'Nome e telefone obrigatórios'}), 400
        
        # Limpar telefone
        phone_clean = ''.join(filter(str.isdigit, phone))
        phone_e164 = f"+55{phone_clean}" if not phone_clean.startswith('55') else f"+{phone_clean}"
        
        # Usar SQL direto
        import sqlite3
        db_path = "instance/medical_bot.db"
        os.makedirs("instance", exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            phone_e164 VARCHAR(20) UNIQUE NOT NULL,
            phone_masked VARCHAR(20),
            email VARCHAR(255),
            birth_date DATE,
            gender CHAR(1),
            priority VARCHAR(20) DEFAULT 'normal',
            notes TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Inserir paciente
        cursor.execute("""
        INSERT OR REPLACE INTO patients 
        (name, phone_e164, phone_masked, email, birth_date, gender, priority, notes, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, phone_e164, phone, 
            data.get('email', ''), data.get('birth_date', '1990-01-01'),
            data.get('gender', 'M'), data.get('priority', 'normal'),
            data.get('notes', ''), 1
        ))
        
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Paciente criado com sucesso',
            'patient': {'id': patient_id, 'name': name, 'phone': phone}
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

'''
    
    # Adiciona antes do if __name__
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'if __name__ == ' in line:
            lines.insert(i, simple_endpoint)
            break
    
    # Escreve arquivo atualizado
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Endpoint simplificado adicionado")
    return True

def create_test_script():
    """Cria script de teste"""
    
    test_content = '''#!/usr/bin/env python3
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
    print(f"\\n{'✅ TESTE PASSOU' if success else '❌ TESTE FALHOU'}")
'''
    
    with open('test_simple_patient.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ Script de teste criado")
    return True

def main():
    print("🔧 CORREÇÃO SIMPLES DO BANCO DE DADOS")
    print("=" * 50)
    
    success = 0
    
    if add_simple_patient_endpoint():
        success += 1
    
    if create_test_script():
        success += 1
    
    if success == 2:
        print("\n✅ CORREÇÃO COMPLETA!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. git add -A && git commit -m 'Add simple patient endpoint' && git push")
        print("2. Aguardar deploy (2 minutos)")
        print("3. python3 test_simple_patient.py")
    
    return success == 2

if __name__ == "__main__":
    main()
