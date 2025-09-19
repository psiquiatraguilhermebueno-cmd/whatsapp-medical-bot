#!/usr/bin/env python3
"""
Script para corrigir problemas na aplicação Railway
"""

import os
import sys

def fix_main_py():
    """
    Corrige problemas no main.py que podem estar causando erro 502
    """
    
    print("🔧 Corrigindo main.py...")
    
    # Ler arquivo atual
    with open('src/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há problemas de sintaxe ou imports
    fixes_applied = []
    
    # 1. Garantir que todos os imports necessários estão presentes
    required_imports = [
        'import os',
        'import sys', 
        'import logging',
        'from flask import Flask, send_from_directory, jsonify, request',
        'import requests',
        'from datetime import datetime'
    ]
    
    for imp in required_imports:
        if imp not in content:
            print(f"⚠️ Import ausente: {imp}")
            # Adicionar import no início do arquivo
            lines = content.split('\n')
            # Encontrar onde adicionar
            for i, line in enumerate(lines):
                if line.startswith('from flask import'):
                    lines.insert(i + 1, imp.replace('from flask import Flask, send_from_directory, jsonify, request', ''))
                    break
            content = '\n'.join(lines)
            fixes_applied.append(f"Adicionado import: {imp}")
    
    # 2. Verificar se há problemas com endpoints duplicados
    endpoint_count = content.count('@app.route(\'/api/send-template\'')
    if endpoint_count > 1:
        print(f"⚠️ Endpoint duplicado encontrado: {endpoint_count} vezes")
        # Remover duplicatas mantendo apenas a última
        parts = content.split('@app.route(\'/api/send-template\'')
        if len(parts) > 2:
            # Manter apenas a primeira parte e a última definição
            content = parts[0] + '@app.route(\'/api/send-template\'' + parts[-1]
            fixes_applied.append("Removidas definições duplicadas de endpoint")
    
    # 3. Verificar se há problemas com indentação ou sintaxe
    try:
        compile(content, 'src/main.py', 'exec')
        print("✅ Sintaxe do main.py está correta")
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe encontrado: {e}")
        print(f"Linha {e.lineno}: {e.text}")
        return False
    
    # 4. Salvar arquivo corrigido
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    if fixes_applied:
        print("✅ Correções aplicadas:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    else:
        print("✅ Nenhuma correção necessária no main.py")
    
    return True

def create_simple_health_check():
    """
    Cria um health check simples para testar se a aplicação está funcionando
    """
    
    simple_app = '''#!/usr/bin/env python3
"""
Aplicação simples para testar se o Railway está funcionando
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'whatsapp-medical-bot',
        'version': '1.0.0'
    })

@app.route('/')
def home():
    return jsonify({
        'message': 'WhatsApp Medical Bot API',
        'status': 'running'
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
'''
    
    with open('simple_app.py', 'w', encoding='utf-8') as f:
        f.write(simple_app)
    
    print("✅ Aplicação simples criada: simple_app.py")

def main():
    """
    Função principal
    """
    print("🔧 CORRIGINDO APLICAÇÃO RAILWAY")
    print("=" * 40)
    
    # 1. Corrigir main.py
    if fix_main_py():
        print("✅ main.py corrigido com sucesso")
    else:
        print("❌ Falha ao corrigir main.py")
        return False
    
    # 2. Criar aplicação simples de backup
    create_simple_health_check()
    
    # 3. Verificar estrutura de arquivos
    print("\n📁 Verificando estrutura de arquivos...")
    required_files = [
        'src/main.py',
        'requirements.txt',
        'railway.json'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - AUSENTE!")
    
    print("\n🎯 CORREÇÕES CONCLUÍDAS!")
    print("Próximos passos:")
    print("1. Fazer commit das correções")
    print("2. Push para o Railway")
    print("3. Aguardar deploy")
    print("4. Testar webhook")
    
    return True

if __name__ == "__main__":
    main()
