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
    return render_template('landing.html')

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
    
    # Sync from json (both entries with username match AND old entries without username)
    if os.path.exists('workout_history.json'):
        try:
            with open('workout_history.json', 'r') as f:
                history = json.load(f)
            for entry in history:
                entry_user = entry.get('username', '')
                # Match entries belonging to this user OR entries without a username
                if entry_user == user.username or (not entry_user and entry.get('exercise')):
                    try:
                        date_obj = datetime.strptime(entry.get('date'), '%Y-%m-%d %H:%M')
                    except Exception:
                        try:
                            date_obj = datetime.strptime(entry.get('date'), '%Y-%m-%d %H:%M:%S')
                        except Exception:
                            continue
                    if not Workout.query.filter_by(user_id=user.id, date=date_obj, exercise_type=entry.get('exercise')).first():
                        dur_str = str(entry.get('duration', '0m 0s'))
                        dur_sec = 0
                        if 'm' in dur_str and 's' in dur_str:
                            parts = dur_str.split('m')
                            m = int(parts[0].strip())
                            s = int(parts[1].replace('s','').strip())
                            dur_sec = m * 60 + s
                        elif dur_str.isdigit():
                            dur_sec = int(dur_str)
                        
                        form = entry.get('form_score', 100)
                        
                        w = Workout(
                            user_id=user.id,
                            date=date_obj,
                            exercise_type=entry.get('exercise'),
                            reps=int(entry.get('reps', 0)),
                            duration=dur_sec,
                            calories=float(entry.get('calories', 0)),
                            form_score=form,
                            notes=entry.get('feedback', '')
                        )
                        db.session.add(w)
            db.session.commit()
        except Exception as e:
            print("Error syncing json:", e)
            
    # Get stats
    total_workouts = Workout.query.filter_by(user_id=user_id).count()
    total_reps = db.session.query(db.func.sum(Workout.reps)).filter_by(user_id=user_id).scalar() or 0
    total_calories = db.session.query(db.func.sum(Workout.calories)).filter_by(user_id=user_id).scalar() or 0
    avg_form_score = db.session.query(db.func.avg(Workout.form_score)).filter_by(user_id=user_id).scalar() or 0
    total_duration = db.session.query(db.func.sum(Workout.duration)).filter_by(user_id=user_id).scalar() or 0
    
    # Recent workouts
    recent_workouts = Workout.query.filter_by(user_id=user_id).order_by(Workout.date.desc()).limit(10).all()
    
    # This week's activity - find which days of the week have workouts
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_workouts_list = Workout.query.filter(
        Workout.user_id == user_id,
        Workout.date >= week_ago
    ).all()
    # Get day-of-week numbers (0=Mon, 6=Sun) that have workouts this week
    workout_weekdays = list(set(w.date.weekday() for w in week_workouts_list))
    
    # Per-exercise breakdown
    exercise_stats = db.session.query(
        Workout.exercise_type,
        db.func.sum(Workout.reps),
        db.func.sum(Workout.calories),
        db.func.count(Workout.id),
        db.func.avg(Workout.form_score)
    ).filter_by(user_id=user_id).group_by(Workout.exercise_type).all()
    
    exercise_breakdown = []
    for ex in exercise_stats:
        exercise_breakdown.append({
            'name': ex[0].replace('_', ' ').title() if ex[0] else 'Unknown',
            'reps': int(ex[1] or 0),
            'calories': round(float(ex[2] or 0), 1),
            'sessions': ex[3],
            'form_score': round(float(ex[4] or 0), 1)
        })
    
    # Format total duration as human readable
    dur_mins = int(total_duration) // 60
    dur_secs = int(total_duration) % 60
    total_duration_str = f"{dur_mins}m {dur_secs}s"
    
    return render_template('dashboard.html', 
                         user=user,
                         total_workouts=total_workouts,
                         total_reps=int(total_reps),
                         total_calories=round(total_calories, 1),
                         avg_form_score=round(avg_form_score, 1),
                         total_duration_str=total_duration_str,
                         recent_workouts=recent_workouts,
                         week_workouts=len(week_workouts_list),
                         workout_weekdays=workout_weekdays,
                         exercise_breakdown=exercise_breakdown,
                         datetime=datetime)

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('calendar.html')

@app.route('/vitals')
def vitals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('vitals.html')

@app.route('/community')
def community():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('community.html')

@app.route('/nutrition')
def nutrition():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('nutrition.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

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

from flask import send_from_directory

@app.route('/trainer_ui')
def trainer_ui():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return send_from_directory('frontend/dist', 'index.html')

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('frontend/dist/assets', path)

@app.route('/start_trainer')
def start_trainer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('web_trainer.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)