from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workouts = db.relationship('Workout', backref='user', lazy=True)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    exercise_type = db.Column(db.String(50), nullable=False)  # squat, pushup, bicep_curl
    reps = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in seconds
    calories = db.Column(db.Float, nullable=False)
    form_score = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))
        
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get stats
    total_workouts = Workout.query.filter_by(user_id=user_id).count()
    total_reps = db.session.query(db.func.sum(Workout.reps)).filter_by(user_id=user_id).scalar() or 0
    total_calories = db.session.query(db.func.sum(Workout.calories)).filter_by(user_id=user_id).scalar() or 0
    avg_form_score = db.session.query(db.func.avg(Workout.form_score)).filter_by(user_id=user_id).scalar() or 0
    
    # Recent workouts
    recent_workouts = Workout.query.filter_by(user_id=user_id).order_by(Workout.date.desc()).limit(10).all()
    
    # This week's activity
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_workouts = Workout.query.filter(
        Workout.user_id == user_id,
        Workout.date >= week_ago
    ).all()
    
    return render_template('dashboard.html', 
                         user=user,
                         total_workouts=total_workouts,
                         total_reps=int(total_reps),
                         total_calories=round(total_calories, 1),
                         avg_form_score=round(avg_form_score, 1),
                         recent_workouts=recent_workouts,
                         week_workouts=len(week_workouts))

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('calendar.html')

@app.route('/api/workouts')
def get_workouts():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    workouts = Workout.query.filter_by(user_id=user_id).all()
    
    workout_data = []
    for w in workouts:
        workout_data.append({
            'id': w.id,
            'date': w.date.strftime('%Y-%m-%d'),
            'exercise': w.exercise_type,
            'reps': w.reps,
            'duration': w.duration,
            'calories': w.calories,
            'form_score': w.form_score
        })
    
    return jsonify(workout_data)

@app.route('/api/add_workout', methods=['POST'])
def add_workout():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_id = session['user_id']
    
    workout = Workout(
        user_id=user_id,
        exercise_type=data['exercise'],
        reps=data['reps'],
        duration=data['duration'],
        calories=data['calories'],
        form_score=data['form_score'],
        notes=data.get('notes', '')
    )
    
    db.session.add(workout)
    db.session.commit()
    
    return jsonify({'success': True, 'workout_id': workout.id})

@app.route('/api/stats')
def get_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    # Exercise breakdown
    exercise_counts = db.session.query(
        Workout.exercise_type, 
        db.func.count(Workout.id),
        db.func.sum(Workout.reps)
    ).filter_by(user_id=user_id).group_by(Workout.exercise_type).all()
    
    exercise_data = {
        'labels': [e[0] for e in exercise_counts],
        'counts': [e[1] for e in exercise_counts],
        'reps': [e[2] for e in exercise_counts]
    }
    
    # Weekly progress (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    daily_workouts = db.session.query(
        db.func.date(Workout.date),
        db.func.count(Workout.id),
        db.func.sum(Workout.calories)
    ).filter(
        Workout.user_id == user_id,
        Workout.date >= week_ago
    ).group_by(db.func.date(Workout.date)).all()
    
    weekly_data = {
        'dates': [str(d[0]) for d in daily_workouts],
        'workouts': [d[1] for d in daily_workouts],
        'calories': [float(d[2] or 0) for d in daily_workouts]
    }
    
    return jsonify({
        'exercise_breakdown': exercise_data,
        'weekly_progress': weekly_data
    })

@app.route('/start_trainer')
def start_trainer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        import subprocess
        import sys
        
        # Get the Python executable and script path
        python_exe = sys.executable
        script_path = os.path.join(os.path.dirname(__file__), 'app.py')
        
        # Check if app.py exists
        if not os.path.exists(script_path):
            flash('Error: app.py not found! Make sure it\'s in the same folder.', 'error')
            return redirect(url_for('dashboard'))
        
        # Launch in a new process
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                [python_exe, script_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=os.path.dirname(script_path)
            )
        else:  # Linux/Mac
            subprocess.Popen([python_exe, script_path])
        
        flash('AI Fitness Trainer launching... Check the new window!', 'success')
    except Exception as e:
        flash(f'Error launching trainer: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)