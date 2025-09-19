"""
Templates WhatsApp para questionários médicos
"""

# Templates para u-ETG (Teste de Triagem de Uso de Álcool)
UETG_TEMPLATES = {
    "start": {
        "name": "uetg_start",
        "template": """🍺 *Teste u-ETG - Triagem de Uso de Álcool*

Olá! É hora do seu teste u-ETG.

Este teste ajuda a avaliar padrões de consumo de álcool.

*Responda com sinceridade:*

*1.* Com que frequência você consome bebidas alcoólicas?

a) Nunca (0 pontos)
b) Mensalmente ou menos (1 ponto)
c) 2-4 vezes por mês (2 pontos)
d) 2-3 vezes por semana (3 pontos)
e) 4 ou mais vezes por semana (4 pontos)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "question_2": {
        "template": """*2.* Quantas doses de álcool você consome num dia normal?

a) 1 ou 2 (0 pontos)
b) 3 ou 4 (1 ponto)
c) 5 ou 6 (2 pontos)
d) 7 a 9 (3 pontos)
e) 10 ou mais (4 pontos)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "question_3": {
        "template": """*3.* Com que frequência você consome seis ou mais doses em uma única ocasião?

a) Nunca (0 pontos)
b) Menos que mensalmente (1 ponto)
c) Mensalmente (2 pontos)
d) Semanalmente (3 pontos)
e) Quase diariamente (4 pontos)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "result_low": {
        "template": """✅ *Resultado u-ETG: BAIXO RISCO*

Pontuação: {score}/12

Seu padrão de consumo de álcool está dentro de limites considerados de baixo risco.

Continue mantendo esse padrão responsável! 👍

_Próximo teste em: {next_test}_"""
    },
    
    "result_medium": {
        "template": """⚠️ *Resultado u-ETG: RISCO MODERADO*

Pontuação: {score}/12

Seu padrão de consumo indica risco moderado. Considere:
• Reduzir a frequência de consumo
• Limitar a quantidade por ocasião
• Buscar atividades alternativas

_Próximo teste em: {next_test}_"""
    },
    
    "result_high": {
        "template": """🚨 *Resultado u-ETG: ALTO RISCO*

Pontuação: {score}/12

Seu padrão indica alto risco. Recomendações:
• Considere buscar ajuda profissional
• Reduza significativamente o consumo
• Converse com seu médico

_Próximo teste em: {next_test}_"""
    }
}

# Templates para GAD-7 (Transtorno de Ansiedade Generalizada)
GAD7_TEMPLATES = {
    "start": {
        "name": "gad7_start",
        "template": """😰 *Escala GAD-7 - Ansiedade*

Olá! É hora da sua avaliação de ansiedade GAD-7.

*Nas últimas 2 semanas, com que frequência você foi incomodado pelos seguintes problemas?*

*1.* Sentir-se nervoso, ansioso ou muito tenso

a) Nenhuma vez (0)
b) Vários dias (1)
c) Mais da metade dos dias (2)
d) Quase todos os dias (3)

Responda apenas com a letra (a, b, c ou d)""",
        "buttons": ["a", "b", "c", "d"]
    },
    
    "questions": [
        "Não conseguir parar ou controlar as preocupações",
        "Preocupar-se muito com diversas coisas",
        "Dificuldade para relaxar",
        "Ficar tão agitado que se torna difícil permanecer parado",
        "Ficar facilmente aborrecido ou irritado",
        "Sentir medo como se algo terrível fosse acontecer"
    ],
    
    "result_minimal": {
        "template": """✅ *Resultado GAD-7: ANSIEDADE MÍNIMA*

Pontuação: {score}/21

Seus níveis de ansiedade estão dentro do normal.

Continue cuidando do seu bem-estar mental! 😊

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_mild": {
        "template": """⚠️ *Resultado GAD-7: ANSIEDADE LEVE*

Pontuação: {score}/21

Você apresenta sintomas leves de ansiedade.

Dicas:
• Pratique técnicas de respiração
• Mantenha rotina de exercícios
• Considere técnicas de relaxamento

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_moderate": {
        "template": """🔶 *Resultado GAD-7: ANSIEDADE MODERADA*

Pontuação: {score}/21

Você apresenta sintomas moderados de ansiedade.

Recomendações:
• Converse com um profissional de saúde
• Pratique mindfulness
• Evite cafeína em excesso

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_severe": {
        "template": """🚨 *Resultado GAD-7: ANSIEDADE SEVERA*

Pontuação: {score}/21

Você apresenta sintomas severos de ansiedade.

*IMPORTANTE:* Procure ajuda profissional imediatamente.
• Converse com seu médico
• Considere terapia psicológica
• Não hesite em buscar suporte

_Próxima avaliação em: {next_test}_"""
    }
}

# Templates para PHQ-9 (Depressão)
PHQ9_TEMPLATES = {
    "start": {
        "name": "phq9_start",
        "template": """😔 *Escala PHQ-9 - Depressão*

Olá! É hora da sua avaliação de humor PHQ-9.

*Nas últimas 2 semanas, com que frequência você foi incomodado pelos seguintes problemas?*

*1.* Pouco interesse ou prazer em fazer as coisas

a) Nenhuma vez (0)
b) Vários dias (1)
c) Mais da metade dos dias (2)
d) Quase todos os dias (3)

Responda apenas com a letra (a, b, c ou d)""",
        "buttons": ["a", "b", "c", "d"]
    },
    
    "questions": [
        "Sentir-se desanimado, deprimido ou sem esperança",
        "Dificuldade para pegar no sono, continuar dormindo ou dormir demais",
        "Sentir-se cansado ou com pouca energia",
        "Falta de apetite ou comer demais",
        "Sentir-se mal consigo mesmo ou sentir que é um fracasso",
        "Dificuldade para se concentrar",
        "Lentidão para se mover ou falar, ou muito agitado",
        "Pensamentos de que seria melhor estar morto ou se ferir"
    ],
    
    "result_minimal": {
        "template": """✅ *Resultado PHQ-9: HUMOR NORMAL*

Pontuação: {score}/27

Seu humor está dentro da normalidade.

Continue cuidando da sua saúde mental! 😊

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_mild": {
        "template": """⚠️ *Resultado PHQ-9: DEPRESSÃO LEVE*

Pontuação: {score}/27

Você apresenta sintomas leves de depressão.

Dicas:
• Mantenha atividades prazerosas
• Pratique exercícios regularmente
• Mantenha contato social

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_moderate": {
        "template": """🔶 *Resultado PHQ-9: DEPRESSÃO MODERADA*

Pontuação: {score}/27

Você apresenta sintomas moderados de depressão.

Recomendações:
• Procure ajuda profissional
• Mantenha rotina estruturada
• Pratique autocuidado

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_severe": {
        "template": """🚨 *Resultado PHQ-9: DEPRESSÃO SEVERA*

Pontuação: {score}/27

Você apresenta sintomas severos de depressão.

*URGENTE:* Procure ajuda profissional imediatamente.
• Converse com seu médico
• Considere terapia
• Entre em contato com suporte de crise se necessário

_Próxima avaliação em: {next_test}_"""
    }
}

# Templates para ASRS-18 (TDAH)
ASRS18_TEMPLATES = {
    "start": {
        "name": "asrs18_start", 
        "template": """🧠 *Escala ASRS-18 - TDAH*

Olá! É hora da sua avaliação ASRS-18 para TDAH.

*Nos últimos 6 meses, com que frequência você teve os seguintes problemas?*

*1.* Dificuldade para se concentrar em trabalho ou atividades de lazer

a) Nunca (0)
b) Raramente (1)
c) Às vezes (2)
d) Frequentemente (3)
e) Muito frequentemente (4)

Responda apenas com a letra (a, b, c, d ou e)""",
        "buttons": ["a", "b", "c", "d", "e"]
    },
    
    "questions": [
        "Dificuldade para organizar tarefas e atividades",
        "Problemas para lembrar de compromissos ou obrigações",
        "Evitar ou adiar tarefas que exigem muito esforço mental",
        "Inquietação com mãos ou pés ou se remexer na cadeira",
        "Sentir-se excessivamente ativo ou compelido a fazer coisas",
        "Cometer erros por falta de atenção quando tem que trabalhar",
        "Dificuldade para manter atenção em tarefas ou atividades",
        "Dificuldade para ouvir quando falam diretamente com você",
        "Não seguir instruções até o fim e não terminar trabalhos",
        "Dificuldade para brincar ou se envolver em atividades de lazer",
        "Estar 'a mil' ou sentir que tem um motor ligado",
        "Falar em excesso",
        "Terminar frases de pessoas que estão falando",
        "Dificuldade para esperar sua vez",
        "Interromper ou se intrometer em conversas",
        "Deixar seu lugar em situações onde deveria ficar sentado",
        "Sentir-se inquieto ou impaciente"
    ],
    
    "result_low": {
        "template": """✅ *Resultado ASRS-18: BAIXO RISCO TDAH*

Pontuação: {score}/72

Seus sintomas não indicam TDAH.

Continue mantendo suas estratégias de organização! 👍

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_moderate": {
        "template": """⚠️ *Resultado ASRS-18: RISCO MODERADO TDAH*

Pontuação: {score}/72

Você apresenta alguns sintomas de TDAH.

Dicas:
• Use listas e lembretes
• Organize seu ambiente
• Pratique técnicas de foco

_Próxima avaliação em: {next_test}_"""
    },
    
    "result_high": {
        "template": """🔶 *Resultado ASRS-18: ALTO RISCO TDAH*

Pontuação: {score}/72

Você apresenta sintomas significativos de TDAH.

Recomendações:
• Procure avaliação com especialista
• Considere estratégias de organização
• Discuta opções de tratamento

_Próxima avaliação em: {next_test}_"""
    }
}

# Função para calcular pontuações
def calculate_scores():
    return {
        "uetg": {
            "low": (0, 3),
            "medium": (4, 7),
            "high": (8, 12)
        },
        "gad7": {
            "minimal": (0, 4),
            "mild": (5, 9),
            "moderate": (10, 14),
            "severe": (15, 21)
        },
        "phq9": {
            "minimal": (0, 4),
            "mild": (5, 9),
            "moderate": (10, 14),
            "severe": (15, 27)
        },
        "asrs18": {
            "low": (0, 23),
            "moderate": (24, 47),
            "high": (48, 72)
        }
    }

# Mensagens de boas-vindas e instruções
WELCOME_MESSAGES = {
    "first_contact": """👋 *Bem-vindo ao Bot Médico!*

Olá! Sou seu assistente para acompanhamento médico.

Você foi cadastrado para receber:
🍺 Teste u-ETG (álcool)
😰 Escala GAD-7 (ansiedade)  
😔 Escala PHQ-9 (depressão)
🧠 Escala ASRS-18 (TDAH)

Os questionários serão enviados conforme sua programação.

Para dúvidas, digite *ajuda*""",
    
    "help": """ℹ️ *Como funciona:*

• Você receberá questionários periodicamente
• Responda com sinceridade para melhor acompanhamento
• Use apenas as opções indicadas (a, b, c, d, e)
• Seus dados são confidenciais

*Comandos:*
• *ajuda* - Esta mensagem
• *status* - Ver próximos questionários
• *contato* - Falar com equipe médica

Em caso de emergência, procure atendimento médico imediato.""",
    
    "invalid_response": """❌ *Resposta inválida*

Por favor, responda apenas com a letra indicada (a, b, c, d ou e).

Se precisar de ajuda, digite *ajuda*""",
    
    "session_timeout": """⏰ *Sessão expirada*

O questionário foi interrompido por inatividade.

Você receberá um novo convite em breve.

Para dúvidas, digite *ajuda*"""
}
