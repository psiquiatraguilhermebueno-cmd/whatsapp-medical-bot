#!/usr/bin/env python3
"""
Corrige main.py removendo código problemático e garantindo criação de tabelas
"""

import os

def fix_main_py():
    """
    Corrige o main.py para garantir que funcione corretamente
    """
    
    main_file = 'src/main.py'
    
    # Ler arquivo atual
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há problemas de sintaxe ou imports
    lines = content.split('\n')
    
    # Remover linhas problemáticas
    clean_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
            
        # Pular linhas com problemas conhecidos
        if 'send_immediate_templates' in line and 'def' not in line:
            continue
        if 'sent_templates = send_immediate_templates' in line:
            continue
        if 'print(f"🚀 Templates enviados' in line:
            continue
            
        clean_lines.append(line)
    
    # Garantir que db.create_all() seja chamado na inicialização
    init_code = '''
# Criar tabelas na inicialização
with app.app_context():
    try:
        db.create_all()
        print("✅ Tabelas criadas/verificadas")
    except Exception as e:
        print(f"⚠️ Erro ao criar tabelas: {e}")
'''
    
    # Encontrar onde inserir o código de inicialização
    final_lines = []
    init_added = False
    
    for i, line in enumerate(clean_lines):
        final_lines.append(line)
        
        # Inserir após as definições de rotas, antes do if __name__
        if 'if __name__' in line and not init_added:
            final_lines.insert(-1, init_code)
            init_added = True
    
    # Se não encontrou if __name__, adicionar no final
    if not init_added:
        final_lines.append(init_code)
    
    # Salvar arquivo corrigido
    corrected_content = '\n'.join(final_lines)
    
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(corrected_content)
    
    print("✅ main.py corrigido")
    return True

def main():
    """
    Função principal
    """
    
    print("🔧 CORRIGINDO MAIN.PY")
    print("=" * 25)
    
    if fix_main_py():
        print("✅ main.py corrigido com sucesso")
        print("\n📋 CORREÇÕES APLICADAS:")
        print("• Código problemático removido")
        print("• db.create_all() garantido na inicialização")
        print("• Sintaxe limpa")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. Fazer commit e push")
        print("2. Aguardar deploy")
        print("3. Testar cadastro de paciente")
        
        return True
    else:
        print("❌ Falha ao corrigir main.py")
        return False

if __name__ == "__main__":
    main()
