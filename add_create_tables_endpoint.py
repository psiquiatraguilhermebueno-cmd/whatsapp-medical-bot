#!/usr/bin/env python3
"""
Script para adicionar endpoint de criação de tabelas ao main.py
"""

def add_create_tables_endpoint():
    """Adiciona endpoint para criar tabelas"""
    
    # Lê o arquivo main.py atual
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Endpoint para criar tabelas
    create_tables_endpoint = '''
@app.route('/admin/api/create-tables', methods=['POST'])
def create_tables():
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
    
    # Encontra onde inserir o endpoint (antes da última linha)
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
    print("🔧 ADICIONANDO ENDPOINT DE CRIAÇÃO DE TABELAS")
    print("=" * 60)
    
    try:
        success = add_create_tables_endpoint()
        
        if success:
            print("✅ Endpoint adicionado com sucesso!")
            print("🚀 Faça commit e push para aplicar a alteração")
            print("\n📋 PRÓXIMOS PASSOS:")
            print("1. git add src/main.py")
            print("2. git commit -m 'Add create-tables endpoint'")
            print("3. git push origin main")
            print("4. Aguardar deploy do Railway")
            print("5. Executar script create_tables_railway.py")
        else:
            print("❌ Falha ao adicionar endpoint")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    return success

if __name__ == "__main__":
    main()
