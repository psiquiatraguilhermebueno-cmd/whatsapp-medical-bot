from flask import Blueprint, request, jsonify
from src.models.mood_chart import MoodChart, BreathingExercise, BreathingSession
from src.models.patient import Patient
from src.models.user import db
from datetime import datetime, date

mood_bp = Blueprint('mood', __name__)

@mood_bp.route('/mood-charts', methods=['GET'])
def get_mood_charts():
    """Listar registros de humor"""
    try:
        patient_id = request.args.get('patient_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = MoodChart.query
        
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(MoodChart.date >= start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(MoodChart.date <= end)
        
        mood_charts = query.order_by(MoodChart.date.desc()).all()
        return jsonify([chart.to_dict() for chart in mood_charts]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/mood-charts', methods=['POST'])
def create_mood_chart():
    """Criar registro de humor"""
    try:
        data = request.get_json()
        
        required_fields = ['patient_id', 'date', 'mood_level', 'functioning_level']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos obrigatórios: patient_id, date, mood_level, functioning_level'}), 400
        
        # Verificar se o paciente existe
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Converter data de string para date
        chart_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Verificar se já existe registro para esta data
        existing_chart = MoodChart.query.filter_by(
            patient_id=data['patient_id'],
            date=chart_date
        ).first()
        
        if existing_chart:
            return jsonify({'error': 'Já existe registro de humor para esta data'}), 400
        
        mood_chart = MoodChart(
            patient_id=data['patient_id'],
            date=chart_date,
            mood_level=data['mood_level'],
            functioning_level=data['functioning_level'],
            sleep_quality=data.get('sleep_quality'),
            sleep_hours=data.get('sleep_hours'),
            anxiety_level=data.get('anxiety_level'),
            irritability_level=data.get('irritability_level'),
            medications_taken=data.get('medications_taken'),
            significant_events=data.get('significant_events'),
            notes=data.get('notes')
        )
        
        db.session.add(mood_chart)
        db.session.commit()
        
        return jsonify(mood_chart.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/mood-charts/<int:chart_id>', methods=['GET'])
def get_mood_chart(chart_id):
    """Obter registro de humor específico"""
    try:
        mood_chart = MoodChart.query.get(chart_id)
        if not mood_chart:
            return jsonify({'error': 'Registro de humor não encontrado'}), 404
        
        return jsonify(mood_chart.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/mood-charts/<int:chart_id>', methods=['PUT'])
def update_mood_chart(chart_id):
    """Atualizar registro de humor"""
    try:
        mood_chart = MoodChart.query.get(chart_id)
        if not mood_chart:
            return jsonify({'error': 'Registro de humor não encontrado'}), 404
        
        data = request.get_json()
        
        # Atualizar campos permitidos
        if 'mood_level' in data:
            mood_chart.mood_level = data['mood_level']
        if 'functioning_level' in data:
            mood_chart.functioning_level = data['functioning_level']
        if 'sleep_quality' in data:
            mood_chart.sleep_quality = data['sleep_quality']
        if 'sleep_hours' in data:
            mood_chart.sleep_hours = data['sleep_hours']
        if 'anxiety_level' in data:
            mood_chart.anxiety_level = data['anxiety_level']
        if 'irritability_level' in data:
            mood_chart.irritability_level = data['irritability_level']
        if 'medications_taken' in data:
            mood_chart.medications_taken = data['medications_taken']
        if 'significant_events' in data:
            mood_chart.significant_events = data['significant_events']
        if 'notes' in data:
            mood_chart.notes = data['notes']
        
        db.session.commit()
        
        return jsonify(mood_chart.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/mood-charts/<int:chart_id>', methods=['DELETE'])
def delete_mood_chart(chart_id):
    """Deletar registro de humor"""
    try:
        mood_chart = MoodChart.query.get(chart_id)
        if not mood_chart:
            return jsonify({'error': 'Registro de humor não encontrado'}), 404
        
        db.session.delete(mood_chart)
        db.session.commit()
        
        return jsonify({'message': 'Registro de humor deletado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/patients/<int:patient_id>/mood-trend', methods=['GET'])
def get_mood_trend(patient_id):
    """Obter tendência de humor de um paciente"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        days = int(request.args.get('days', 7))
        
        from src.services.mood_service import MoodService
        mood_service = MoodService()
        
        report = mood_service.get_mood_trend_report(patient, days)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/breathing-exercises', methods=['GET'])
def get_breathing_exercises():
    """Listar exercícios de respiração"""
    try:
        category = request.args.get('category')
        
        query = BreathingExercise.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        exercises = query.all()
        return jsonify([exercise.to_dict() for exercise in exercises]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/breathing-exercises/<int:exercise_id>', methods=['GET'])
def get_breathing_exercise(exercise_id):
    """Obter exercício de respiração específico"""
    try:
        exercise = BreathingExercise.query.get(exercise_id)
        if not exercise:
            return jsonify({'error': 'Exercício não encontrado'}), 404
        
        return jsonify(exercise.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/breathing-sessions', methods=['POST'])
def create_breathing_session():
    """Criar sessão de exercício de respiração"""
    try:
        data = request.get_json()
        
        required_fields = ['patient_id', 'exercise_id']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos obrigatórios: patient_id, exercise_id'}), 400
        
        # Verificar se o paciente existe
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Verificar se o exercício existe
        exercise = BreathingExercise.query.get(data['exercise_id'])
        if not exercise:
            return jsonify({'error': 'Exercício não encontrado'}), 404
        
        session = BreathingSession(
            patient_id=data['patient_id'],
            exercise_id=data['exercise_id'],
            start_time=datetime.utcnow(),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            completed=data.get('completed', False),
            rating=data.get('rating'),
            notes=data.get('notes')
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify(session.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/breathing-sessions/<int:session_id>', methods=['PUT'])
def update_breathing_session(session_id):
    """Atualizar sessão de exercício de respiração"""
    try:
        session = BreathingSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        data = request.get_json()
        
        if 'end_time' in data:
            session.end_time = datetime.fromisoformat(data['end_time']) if data['end_time'] else None
        if 'completed' in data:
            session.completed = data['completed']
        if 'rating' in data:
            session.rating = data['rating']
        if 'notes' in data:
            session.notes = data['notes']
        
        db.session.commit()
        
        return jsonify(session.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mood_bp.route('/patients/<int:patient_id>/breathing-sessions', methods=['GET'])
def get_patient_breathing_sessions(patient_id):
    """Obter sessões de respiração de um paciente"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        sessions = BreathingSession.query.filter_by(patient_id=patient_id).order_by(BreathingSession.start_time.desc()).all()
        
        return jsonify([session.to_dict() for session in sessions]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

