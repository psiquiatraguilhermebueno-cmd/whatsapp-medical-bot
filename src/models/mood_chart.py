from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from src.models.user import db

class MoodChart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # Data do registro
    
    # Escala de humor (-3 a +3, baseada no NIMH Life Chart)
    # -3: Depressão severa, -2: Depressão moderada, -1: Depressão leve
    # 0: Humor normal/eutímico
    # +1: Hipomania leve, +2: Hipomania moderada, +3: Mania severa
    mood_level = db.Column(db.Integer, nullable=False)  # -3 a +3
    
    # Nível de funcionamento (0-100)
    functioning_level = db.Column(db.Integer, nullable=False)  # 0-100
    
    # Qualidade do sono (1-5)
    sleep_quality = db.Column(db.Integer, nullable=True)  # 1: Muito ruim, 5: Excelente
    sleep_hours = db.Column(db.Float, nullable=True)  # Horas de sono
    
    # Nível de ansiedade (0-10)
    anxiety_level = db.Column(db.Integer, nullable=True)  # 0: Nenhuma, 10: Extrema
    
    # Nível de irritabilidade (0-10)
    irritability_level = db.Column(db.Integer, nullable=True)  # 0: Nenhuma, 10: Extrema
    
    # Medicações tomadas
    medications_taken = db.Column(db.JSON, nullable=True)  # Lista de medicações
    
    # Eventos significativos
    significant_events = db.Column(db.Text, nullable=True)  # Eventos do dia
    
    # Observações livres
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MoodChart {self.date} - Mood: {self.mood_level}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'date': self.date.isoformat() if self.date else None,
            'mood_level': self.mood_level,
            'mood_description': self.get_mood_description(),
            'functioning_level': self.functioning_level,
            'sleep_quality': self.sleep_quality,
            'sleep_hours': self.sleep_hours,
            'anxiety_level': self.anxiety_level,
            'irritability_level': self.irritability_level,
            'medications_taken': self.medications_taken,
            'significant_events': self.significant_events,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_mood_description(self):
        """Retorna a descrição textual do nível de humor"""
        mood_descriptions = {
            -3: "Depressão severa",
            -2: "Depressão moderada", 
            -1: "Depressão leve",
            0: "Humor normal/estável",
            1: "Hipomania leve",
            2: "Hipomania moderada",
            3: "Mania severa"
        }
        return mood_descriptions.get(self.mood_level, "Não definido")

class BreathingExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Nome do exercício
    description = db.Column(db.Text, nullable=False)  # Descrição
    duration_minutes = db.Column(db.Integer, nullable=False)  # Duração em minutos
    audio_file_path = db.Column(db.String(500), nullable=True)  # Caminho do arquivo de áudio
    instructions = db.Column(db.JSON, nullable=False)  # Instruções passo a passo
    category = db.Column(db.String(50), nullable=False)  # Categoria (relaxamento, ansiedade, etc.)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BreathingExercise {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'audio_file_path': self.audio_file_path,
            'instructions': self.instructions,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BreathingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('breathing_exercise.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer, nullable=True)  # Avaliação do exercício (1-5)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BreathingSession {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'exercise_id': self.exercise_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'completed': self.completed,
            'rating': self.rating,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

