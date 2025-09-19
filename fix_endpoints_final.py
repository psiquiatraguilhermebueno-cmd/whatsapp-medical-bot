#!/usr/bin/env python3
"""
Script para corrigir endpoints de pacientes e adicionar criação de tabelas
"""

def fix_patient_endpoint():
    """Corrige autenticação do endpoint de pacientes"""
    
    # Lê o arquivo main.py atual
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substitui a autenticação Bearer por X-Admin-Token
    old_auth = '''        # Verificar token admin
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autorização necessário'}), 401
        
        token = auth_header.split(' ')[1]
        if token != os.getenv('ADMIN_UI_TOKEN', 'admin123456'):
            return jsonify({'error': 'Token inválido'}), 401'''
    
    new_auth = '''        # Verificar token admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin123456':
            return jsonify({'error': 'Unauthorized', 'success': False}), 401'''
    
    content = content.replace(old_auth, new_auth)
    
    # Escreve o arquivo atualizado
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Autenticação do endpoint de pacientes corrigida")
    return True

def add_create_tables_endpoint():
    """Adiciona endpoint para criar tabelas"""
    
    # Lê o arquivo main.py atual
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Endpoint para criar tabelas
    create_tables_endpoint = '''
@app.route('/admin/api/create-tables', methods=['POST'])
def create_tables_endpoint():
    """Força criação de todas as tabelas do banco"""
    try:
        # Verifica autenticação admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin123456':
            return jsonify({"error": "Unauthorized", "success": False}), 401
        
        # Cria todas as tabelas
        with app.app_context():
            db.create_all()
        
        # Verifica se as tabelas foram criadas
        tables_created = []
        inspector = db.inspect(db.engine)
        
        expected_tables = ['patients', 'responses', 'schedules']
        for table_name in expected_tables:
            if inspector.has_table(table_name):
                tables_created.append(table_name)
        
        return jsonify({
            "success": True,
            "message": "Tabelas criadas com sucesso",
            "tables_created": tables_created,
            "total_tables": len(tables_created)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao criar tabelas: {str(e)}",
            "success": False
        }), 500

'''
    
    # Encontra onde inserir o endpoint (antes da linha que contém "if __name__ == '__main__':")
    lines = content.split('\n')
    
    # Procura pela linha que contém "if __name__ == '__main__':"
    insert_index = -1
    for i, line in enumerate(lines):
        if 'if __name__ == ' in line:
            insert_index = i
            break
    
    if insert_index == -1:
        # Se não encontrar, adiciona no final
        insert_index = len(lines)
    
    # Insere o endpoint
    lines.insert(insert_index, create_tables_endpoint)
    
    # Escreve o arquivo atualizado
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Endpoint /admin/api/create-tables adicionado ao main.py")
    return True

def main():
    """Função principal"""
    print("🔧 CORREÇÃO FINAL DE ENDPOINTS")
    print("=" * 60)
    
    try:
        # 1. Corrigir autenticação do endpoint de pacientes
        fix_patient_endpoint()
        
        # 2. Adicionar endpoint de criação de tabelas
        add_create_tables_endpoint()
        
        print("\n✅ CORREÇÕES APLICADAS COM SUCESSO!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. git add src/main.py")
        print("2. git commit -m 'Fix endpoints authentication and add create-tables'")
        print("3. git push origin main")
        print("4. Aguardar deploy do Railway")
        print("5. Executar script create_tables_railway.py")
        
        return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    main()
