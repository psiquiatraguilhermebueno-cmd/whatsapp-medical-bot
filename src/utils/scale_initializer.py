from src.models.scale import Scale
from src.models.user import db

def initialize_scales():
    """Inicializar as escalas clínicas no banco de dados"""
    
    # Verificar se as escalas já existem
    if Scale.query.filter_by(name='PHQ-9').first():
        print("Escalas já inicializadas")
        return
    
    # PHQ-9
    phq9_questions = [
        "Pouco interesse ou prazer em fazer as coisas",
        "Sentir-se para baixo, deprimido ou sem esperança",
        "Dificuldade em adormecer ou permanecer dormindo, ou dormir demais",
        "Sentir-se cansado ou com pouca energia",
        "Falta de apetite ou comer demais",
        "Sentir-se mal consigo mesmo - ou que você é um fracasso ou decepcionou a si mesmo ou sua família",
        "Dificuldade de concentração em coisas, como ler o jornal ou assistir televisão",
        "Mover-se ou falar tão lentamente que outras pessoas poderiam ter notado? Ou o oposto - estar tão inquieto ou agitado que você tem se movimentado muito mais do que o normal",
        "Pensamentos de que seria melhor estar morto ou de se machucar de alguma forma"
    ]
    
    phq9_scoring_rules = [
        {"min_score": 0, "max_score": 4, "category": "Depressão mínima"},
        {"min_score": 5, "max_score": 9, "category": "Depressão leve"},
        {"min_score": 10, "max_score": 14, "category": "Depressão moderada"},
        {"min_score": 15, "max_score": 19, "category": "Depressão moderadamente severa"},
        {"min_score": 20, "max_score": 27, "category": "Depressão severa"}
    ]
    
    phq9 = Scale(
        name='PHQ-9',
        title='Questionário de Saúde do Paciente - 9',
        description='Escala para avaliação de sintomas depressivos nas últimas 2 semanas',
        questions=phq9_questions,
        scoring_rules=phq9_scoring_rules,
        alarm_threshold=15  # Depressão moderadamente severa ou severa
    )
    
    # GAD-7
    gad7_questions = [
        "Sentir-se nervoso, ansioso ou no limite",
        "Não ser capaz de parar ou controlar a preocupação",
        "Preocupar-se demais com coisas diferentes",
        "Dificuldade em relaxar",
        "Ficar tão inquieto que é difícil ficar parado",
        "Ficar facilmente aborrecido ou irritado",
        "Sentir medo, como se algo terrível pudesse acontecer"
    ]
    
    gad7_scoring_rules = [
        {"min_score": 0, "max_score": 4, "category": "Ansiedade mínima"},
        {"min_score": 5, "max_score": 9, "category": "Ansiedade leve"},
        {"min_score": 10, "max_score": 14, "category": "Ansiedade moderada"},
        {"min_score": 15, "max_score": 21, "category": "Ansiedade severa"}
    ]
    
    gad7 = Scale(
        name='GAD-7',
        title='Transtorno de Ansiedade Generalizada - 7',
        description='Escala para avaliação de sintomas de ansiedade nas últimas 2 semanas',
        questions=gad7_questions,
        scoring_rules=gad7_scoring_rules,
        alarm_threshold=15  # Ansiedade severa
    )
    
    # MDQ - Mood Disorder Questionnaire
    mdq_questions = [
        "Você se sentiu tão bem ou tão animado que outras pessoas pensaram que você não era seu eu normal ou você estava tão animado que se meteu em problemas?",
        "Você estava tão irritado que gritou com pessoas ou começou brigas ou discussões?",
        "Você se sentiu muito mais autoconfiante do que o usual?",
        "Você dormiu muito menos do que o usual e descobriu que realmente não sentia falta disso?",
        "Você estava muito mais falante ou falou mais rápido do que o usual?",
        "Os pensamentos corriam pela sua cabeça ou você não conseguia diminuir o ritmo da sua mente?",
        "Você se distraía tão facilmente com as coisas ao seu redor que tinha problemas para se concentrar ou permanecer no caminho?",
        "Você tinha muito mais energia do que o usual?",
        "Você estava muito mais ativo ou fez muito mais coisas do que o usual?",
        "Você estava muito mais social ou extrovertido do que o usual, por exemplo, telefonou para amigos no meio da noite?",
        "Você estava muito mais interessado em sexo do que o usual?",
        "Você fez coisas que eram incomuns para você ou que outras pessoas poderiam ter pensado que eram excessivas, tolas ou arriscadas?",
        "Gastar dinheiro colocou você ou sua família em apuros?"
    ]
    
    mdq_scoring_rules = [
        {"min_score": 0, "max_score": 6, "category": "Triagem negativa"},
        {"min_score": 7, "max_score": 13, "category": "Triagem positiva para transtorno bipolar"}
    ]
    
    mdq = Scale(
        name='MDQ',
        title='Questionário de Transtorno do Humor',
        description='Escala de triagem para transtorno bipolar',
        questions=mdq_questions,
        scoring_rules=mdq_scoring_rules,
        alarm_threshold=7  # 7 ou mais respostas positivas
    )
    
    # ASRS - Adult ADHD Self-Report Scale (Parte A)
    asrs_questions = [
        "Dificuldade para terminar os detalhes finais de um projeto, uma vez que as partes desafiadoras foram feitas?",
        "Dificuldade para colocar as coisas em ordem quando você tem que fazer uma tarefa que requer organização?",
        "Problemas para lembrar de compromissos ou obrigações?",
        "Quando você tem uma tarefa que requer muito pensamento, você evita ou adia começar?",
        "Inquietação ou mexer com as mãos ou pés quando você tem que ficar sentado por muito tempo?",
        "Sentir-se excessivamente ativo e compelido a fazer coisas, como se fosse movido por um motor?"
    ]
    
    asrs_scoring_rules = [
        {"min_score": 0, "max_score": 3, "category": "Baixa probabilidade de TDAH"},
        {"min_score": 4, "max_score": 24, "category": "Alta probabilidade de TDAH"}
    ]
    
    asrs = Scale(
        name='ASRS',
        title='Escala de Auto-Relato de TDAH em Adultos',
        description='Escala de triagem para TDAH em adultos (últimos 6 meses)',
        questions=asrs_questions,
        scoring_rules=asrs_scoring_rules,
        alarm_threshold=4  # 4 ou mais pontos nas questões críticas
    )
    
    # AUDIT - Alcohol Use Disorders Identification Test
    audit_questions = [
        "Com que frequência você consome bebidas alcoólicas?",
        "Quantas doses de álcool você consome num dia normal?",
        "Com que frequência você consome seis ou mais doses em uma ocasião?",
        "Quantas vezes, durante o último ano, você achou que não conseguiria parar de beber uma vez que havia começado?",
        "Quantas vezes, durante o último ano, você não conseguiu cumprir com o que era esperado de você por causa da bebida?",
        "Quantas vezes, durante o último ano, você precisou beber pela manhã para se sentir bem ao longo do dia após ter bebido muito no dia anterior?",
        "Quantas vezes, durante o último ano, você se sentiu culpado ou com remorso após ter bebido?",
        "Quantas vezes, durante o último ano, você foi incapaz de lembrar o que aconteceu na noite anterior por causa da bebida?",
        "Você já se machucou ou machucou alguém como resultado da sua bebida?",
        "Algum parente, amigo, médico ou outro profissional da saúde já demonstrou preocupação com o seu modo de beber ou sugeriu que você parasse?"
    ]
    
    audit_scoring_rules = [
        {"min_score": 0, "max_score": 7, "category": "Baixo risco"},
        {"min_score": 8, "max_score": 15, "category": "Risco moderado"},
        {"min_score": 16, "max_score": 19, "category": "Alto risco"},
        {"min_score": 20, "max_score": 40, "category": "Possível dependência"}
    ]
    
    audit = Scale(
        name='AUDIT',
        title='Teste de Identificação de Transtornos do Uso de Álcool',
        description='Escala para identificação de problemas relacionados ao uso de álcool',
        questions=audit_questions,
        scoring_rules=audit_scoring_rules,
        alarm_threshold=16  # Alto risco ou possível dependência
    )
    
    # DAST-10 - Drug Abuse Screening Test
    dast_questions = [
        "Você usou drogas além daquelas necessárias por razões médicas?",
        "Você usa mais de uma droga por vez?",
        "Você sempre consegue parar de usar drogas quando quer? (Se nunca usa drogas, responda 'Sim')",
        "Você já teve blackouts ou flashbacks como resultado do uso de drogas?",
        "Você já se sentiu mal ou culpado sobre o seu uso de drogas? (Se nunca usa drogas, responda 'Não')",
        "Seu cônjuge (ou pais) já reclamou sobre seu envolvimento com drogas?",
        "Você negligenciou sua família por causa do seu uso de drogas?",
        "Você se envolveu em atividades ilegais para obter drogas?",
        "Você já experimentou sintomas de abstinência (se sentiu mal) quando parou de usar drogas?",
        "Você teve problemas médicos como resultado do seu uso de drogas (por exemplo, perda de memória, hepatite, convulsões, sangramento)?"
    ]
    
    dast_scoring_rules = [
        {"min_score": 0, "max_score": 0, "category": "Nenhum problema relatado"},
        {"min_score": 1, "max_score": 2, "category": "Baixo nível"},
        {"min_score": 3, "max_score": 5, "category": "Nível moderado"},
        {"min_score": 6, "max_score": 8, "category": "Nível substancial"},
        {"min_score": 9, "max_score": 10, "category": "Nível severo"}
    ]
    
    dast = Scale(
        name='DAST-10',
        title='Teste de Triagem de Abuso de Drogas',
        description='Escala para identificação de problemas relacionados ao uso de drogas (últimos 12 meses)',
        questions=dast_questions,
        scoring_rules=dast_scoring_rules,
        alarm_threshold=6  # Nível substancial ou severo
    )
    
    # Adicionar todas as escalas ao banco de dados
    scales = [phq9, gad7, mdq, asrs, audit, dast]
    for scale in scales:
        db.session.add(scale)
    
    db.session.commit()
    
    print("Escalas PHQ-9, GAD-7, MDQ, ASRS, AUDIT e DAST-10 inicializadas com sucesso!")

