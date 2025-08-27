from src.models.user import db
from src.models.breathing_exercise import BreathingExercise

def initialize_breathing_exercises():
    """Inicializar exercícios de respiração pré-definidos no banco de dados"""
    
    # Verificar se os exercícios já existem
    if BreathingExercise.query.first():
        print("Exercícios de respiração já inicializados")
        return
    
    # Exercício 1: Respiração 4-7-8
    exercise_478 = BreathingExercise(
        name="Respiração 4-7-8",
        description="Técnica de respiração para relaxamento e redução da ansiedade. Inspire por 4, segure por 7, expire por 8.",
        duration_minutes=5,
        instructions="""1. Encontre uma posição confortável, sentado ou deitado
2. Coloque a ponta da língua atrás dos dentes superiores
3. Expire completamente pela boca fazendo um som de 'whoosh'
4. Feche a boca e inspire pelo nariz contando até 4
5. Segure a respiração contando até 7
6. Expire completamente pela boca contando até 8, fazendo o som 'whoosh'
7. Repita o ciclo 3-4 vezes""",
        is_active=True
    )
    
    # Exercício 2: Respiração Quadrada (Box Breathing)
    exercise_box = BreathingExercise(
        name="Respiração Quadrada",
        description="Técnica de respiração para foco e controle da ansiedade. Inspire, segure, expire e segure por 4 tempos cada.",
        duration_minutes=10,
        instructions="""1. Sente-se confortavelmente com as costas retas
2. Expire completamente
3. Inspire lentamente pelo nariz contando até 4
4. Segure a respiração contando até 4
5. Expire lentamente pela boca contando até 4
6. Segure os pulmões vazios contando até 4
7. Repita por 5-10 minutos""",
        is_active=True
    )
    
    # Exercício 3: Respiração Diafragmática
    exercise_diaphragmatic = BreathingExercise(
        name="Respiração Diafragmática",
        description="Respiração profunda usando o diafragma para relaxamento e redução do estresse.",
        duration_minutes=15,
        instructions="""1. Deite-se confortavelmente ou sente-se com as costas retas
2. Coloque uma mão no peito e outra no abdômen
3. Inspire lentamente pelo nariz, fazendo o abdômen subir
4. O peito deve se mover minimamente
5. Expire lentamente pela boca, contraindo suavemente o abdômen
6. Continue por 10-15 minutos""",
        is_active=True
    )
    
    # Exercício 4: Respiração Alternada (Nadi Shodhana)
    exercise_alternate = BreathingExercise(
        name="Respiração Alternada",
        description="Técnica de yoga para equilibrar o sistema nervoso e acalmar a mente.",
        duration_minutes=10,
        instructions="""1. Sente-se confortavelmente com a coluna ereta
2. Use o polegar direito para fechar a narina direita
3. Inspire pela narina esquerda contando até 4
4. Feche a narina esquerda com o dedo anelar
5. Abra a narina direita e expire contando até 4
6. Inspire pela narina direita contando até 4
7. Feche a narina direita e expire pela esquerda
8. Continue alternando por 5-10 minutos""",
        is_active=True
    )
    
    # Exercício 5: Respiração de Coerência Cardíaca
    exercise_coherence = BreathingExercise(
        name="Coerência Cardíaca",
        description="Respiração ritmada para sincronizar coração e mente, reduzindo estresse.",
        duration_minutes=5,
        instructions="""1. Sente-se confortavelmente com as costas retas
2. Inspire lentamente pelo nariz contando até 5
3. Expire lentamente pela boca contando até 5
4. Mantenha um ritmo constante e suave
5. Foque na região do coração
6. Continue por 5 minutos, 6 respirações por minuto""",
        is_active=True
    )
    
    # Exercício 6: Respiração Energizante
    exercise_energizing = BreathingExercise(
        name="Respiração Energizante",
        description="Técnica para aumentar energia e vitalidade, ideal para começar o dia.",
        duration_minutes=3,
        instructions="""1. Fique em pé com os pés afastados na largura dos ombros
2. Inspire profundamente pelo nariz levantando os braços
3. Expire vigorosamente pela boca abaixando os braços
4. Faça respirações rápidas e energéticas
5. Continue por 1-3 minutos
6. Termine com 3 respirações profundas e lentas""",
        is_active=True
    )
    
    # Adicionar todos os exercícios ao banco de dados
    exercises = [
        exercise_478,
        exercise_box,
        exercise_diaphragmatic,
        exercise_alternate,
        exercise_coherence,
        exercise_energizing
    ]
    
    for exercise in exercises:
        db.session.add(exercise)
    
    try:
        db.session.commit()
        print("Exercícios de respiração inicializados com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inicializar exercícios de respiração: {e}")

