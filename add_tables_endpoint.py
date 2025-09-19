#!/usr/bin/env python3
"""
Adiciona endpoint para criar tabelas no main.py
"""

import os

def add_create_tables_endpoint():
    """
    Adiciona endpoint /admin/create-tables ao main.py
    """
    
    main_file = 'src/main.py'
    
    if not os.path.exists(main_file):
        print(f"❌ Arquivo {main_file} não encontrado")
        return False
    
    # Ler arquivo atual
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Endpoint para criar tabelas
    create_tables_endpoint = '''
@app.route('/admin/create-tables', methods=['POST'])
def create_tables():
    """
    Força criação de todas as tabelas do banco de dados
    """
    try:
        # Verificar token admin
        token = request.headers.get('X-Admin-Token')
        if token != os.getenv('ADMIN_UI_TOKEN', 'admin123456'):
            return jsonify({'error': 'Token inválido'}), 401
        
        # Criar todas as tabelas
        with app.app_context():
            db.create_all()
        
        # SQL adicional para garantir estrutura correta
        additional_sql = [
            """CREATE TABLE IF NOT EXISTS patients (
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
            )""",
            """CREATE TABLE IF NOT EXISTS patient_protocols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                protocol_type VARCHAR(50) NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                frequency VARCHAR(20),
                time_of_day TIME,
                immediate_dispatch BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )""",
            """CREATE TABLE IF NOT EXISTS questionnaire_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                questionnaire_type VARCHAR(50) NOT NULL,
                responses TEXT,
                score INTEGER,
                risk_level VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )"""
        ]
        
        # Executar SQL adicional
        for sql in additional_sql:
            try:
                db.session.execute(text(sql))
                db.session.commit()
            except Exception as e:
                print(f"SQL executado (pode já existir): {e}")
        
        return jsonify({
            'success': True,
            'message': 'Tabelas criadas com sucesso',
            'tables': ['patients', 'patient_protocols', 'questionnaire_responses']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''
    
    # Verificar se endpoint já existe
    if '/admin/create-tables' in content:
        print("✅ Endpoint de criação de tabelas já existe")
        return True
    
    # Encontrar onde inserir (antes do if __name__)
    lines = content.split('\n')
    insert_pos = len(lines) - 1
    
    for i, line in enumerate(lines):
        if 'if __name__' in line:
            insert_pos = i
            break
    
    # Inserir endpoint
    lines.insert(insert_pos, create_tables_endpoint)
    content = '\n'.join(lines)
    
    # Salvar arquivo
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Endpoint de criação de tabelas adicionado")
    return True

def main():
    """
    Função principal
    """
    
    print("🔧 ADICIONANDO ENDPOINT DE CRIAÇÃO DE TABELAS")
    print("=" * 45)
    
    # Adicionar endpoint
    if add_create_tables_endpoint():
        print("✅ Endpoint adicionado com sucesso")
        
        print("\n📋 ENDPOINT CRIADO:")
        print("• URL: /admin/create-tables")
        print("• Método: POST")
        print("• Autenticação: X-Admin-Token")
        print("• Função: Cria todas as tabelas do banco")
        
        return True
    else:
        print("❌ Falha ao adicionar endpoint")
        return False

if __name__ == "__main__":
    main()
