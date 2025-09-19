#!/usr/bin/env python3
"""
Criar versão de emergência que funcione via texto simples
"""

emergency_code = '''
# VERSÃO DE EMERGÊNCIA - GAD-7 VIA TEXTO SIMPLES

def emergency_gad7_handler(phone_number, text_body):
    """Handler de emergência para GAD-7 via texto simples"""
    text_lower = text_body.lower().strip()
    
    # Comandos especiais
    if text_lower == 'gad7':
        # Enviar todas as perguntas de uma vez
        all_questions = """📋 *QUESTIONÁRIO GAD-7 COMPLETO*

Responda TODAS as 7 perguntas abaixo com números de 0 a 3:
• 0 = Nenhuma vez
• 1 = Vários dias  
• 2 = Mais da metade dos dias
• 3 = Quase todos os dias

*FORMATO DE RESPOSTA:* Digite os 7 números separados por espaço
Exemplo: 1 2 0 3 1 2 1

*PERGUNTAS:*

1. Sentir-se nervoso, ansioso ou muito tenso?
2. Não conseguir parar ou controlar as preocupações?
3. Preocupar-se muito com diversas coisas?
4. Ter dificuldade para relaxar?
5. Ficar tão agitado que se torna difícil permanecer parado?
6. Ficar facilmente aborrecido ou irritado?
7. Sentir medo como se algo terrível fosse acontecer?

*Responda com 7 números separados por espaço.*"""
        
        return send_whatsapp_message(phone_number, all_questions)
    
    # Verificar se é resposta do GAD-7 (7 números)
    if text_body.strip() and all(c.isdigit() or c.isspace() for c in text_body.strip()):
        numbers = text_body.strip().split()
        
        if len(numbers) == 7 and all(n in ['0', '1', '2', '3'] for n in numbers):
            # Processar resposta completa
            total_score = sum(int(n) for n in numbers)
            
            # Categorizar resultado
            if total_score <= 4:
                category = "Ansiedade mínima"
                interpretation = "Seus sintomas de ansiedade estão em um nível muito baixo."
            elif total_score <= 9:
                category = "Ansiedade leve"
                interpretation = "Você apresenta sintomas leves de ansiedade."
            elif total_score <= 14:
                category = "Ansiedade moderada"
                interpretation = "Você apresenta sintomas moderados de ansiedade. Considere conversar com um profissional."
            else:
                category = "Ansiedade severa"
                interpretation = "Você apresenta sintomas severos de ansiedade. É recomendado buscar ajuda profissional."
            
            result_message = f"""📊 *RESULTADO GAD-7*

*Suas respostas:* {' '.join(numbers)}
*Pontuação total:* {total_score}/21
*Categoria:* {category}

*Interpretação:* {interpretation}

*Data:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Obrigado por responder o questionário! 🙏

Digite *gad7* para fazer um novo questionário."""
            
            return send_whatsapp_message(phone_number, result_message)
    
    return False
'''

# Ler o arquivo main.py atual
with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'r') as f:
    content = f.read()

# Adicionar handler de emergência
if 'def emergency_gad7_handler' not in content:
    # Encontrar onde inserir (após as outras funções)
    insert_point = content.find('def process_text_message(')
    if insert_point != -1:
        new_content = content[:insert_point] + emergency_code + '\n\n' + content[insert_point:]
        
        # Modificar process_text_message para usar o handler de emergência
        new_content = new_content.replace(
            'if text_lower == \'gad7\':',
            '''# Tentar handler de emergência primeiro
    if emergency_gad7_handler(phone_number, text_body):
        return True
    
    if text_lower == 'gad7':'''
        )
        
        # Escrever arquivo atualizado
        with open('/home/ubuntu/whatsapp-medical-bot/src/main.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Versão de emergência adicionada!")
    else:
        print("❌ Não foi possível encontrar ponto de inserção")
else:
    print("⚠️ Versão de emergência já existe")
