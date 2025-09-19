#!/usr/bin/env python3
"""
Script para forçar criação de tabelas na inicialização da aplicação
"""

def add_force_create_tables():
    """Adiciona código para forçar criação de tabelas na inicialização"""
    
    # Lê o arquivo main.py atual
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Código para forçar criação de tabelas
    force_create_code = '''
    # FORÇA CRIAÇÃO DE TABELAS (ADICIONADO AUTOMATICAMENTE)
    try:
        with app.app_context():
            # Força criação de todas as tabelas
            db.create_all()
            
            # Verifica se as tabelas foram criadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"✅ Tabelas disponíveis: {tables}")
            
            # Verifica tabelas essenciais
            essential_tables = ['patients', 'responses', 'schedules']
            missing_tables = [t for t in essential_tables if t not in tables]
            
            if missing_tables:
                logger.warning(f"⚠️ Tabelas ausentes: {missing_tables}")
                # Tenta criar novamente
                db.create_all()
                logger.info("🔄 Tentativa adicional de criação de tabelas")
            else:
                logger.info("✅ Todas as tabelas essenciais estão presentes")
                
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        # Continua mesmo com erro para não quebrar a aplicação
'''
    
    # Encontra onde inserir o código (após a criação do app e antes do if __name__)
    lines = content.split('\n')
    
    # Procura pela linha que contém "create_tables()" ou similar
    insert_index = -1
    for i, line in enumerate(lines):
        if 'create_tables()' in line and 'def ' not in line:
            insert_index = i + 1
            break
    
    if insert_index == -1:
        # Se não encontrar, procura por "if __name__ == '__main__':"
        for i, line in enumerate(lines):
            if 'if __name__ == ' in line:
                insert_index = i
                break
    
    if insert_index == -1:
        # Se ainda não encontrar, adiciona no final
        insert_index = len(lines)
    
    # Insere o código
    lines.insert(insert_index, force_create_code)
    
    # Escreve o arquivo atualizado
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Código de criação forçada de tabelas adicionado ao main.py")
    return True

def main():
    """Função principal"""
    print("🔧 FORÇANDO CRIAÇÃO DE TABELAS NA INICIALIZAÇÃO")
    print("=" * 60)
    
    try:
        success = add_force_create_tables()
        
        if success:
            print("✅ Modificação aplicada com sucesso!")
            print("\n📋 PRÓXIMOS PASSOS:")
            print("1. git add src/main.py")
            print("2. git commit -m 'Force table creation on startup'")
            print("3. git push origin main")
            print("4. Aguardar deploy do Railway")
            print("5. Testar registro de paciente")
            
            print("\n🔍 O QUE FOI FEITO:")
            print("• Adicionado código para criar tabelas automaticamente")
            print("• Verificação de tabelas essenciais")
            print("• Logs detalhados para debug")
            print("• Tratamento de erros para não quebrar a aplicação")
        else:
            print("❌ Falha ao aplicar modificação")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    return success

if __name__ == "__main__":
    main()
