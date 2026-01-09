import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import mediapipe as mp
import numpy as np
import time
import json
import os
import math
import threading
from datetime import datetime
import pyttsx3
from collections import Counter


class InteractiveFitnessTrainer:
    def __init__(self, username, coach_name=None):
        self.username = username
        self.coach_name = coach_name  
        
       
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 160)
            self.engine.setProperty('volume', 1.0)
        except: print("Voice Engine Error")
        
        self.last_speech = 0
        self.speech_cooldown = 2.5
        
        # AI Setup
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # Game State
        self.exercise = "squat"
        self.counter = 0
        self.stage = None
        self.feedback = "Stand in frame"
        self.form_score = 100
        self.total_calories = 0
        self.workout_start_time = None
        self.running = False
        
        self.mistake_history = []
        self.last_error_time = 0
        self.final_report = ""
        
        self.calories_map = {
            "squat": 0.5, "pushup": 0.35, "bicep_curl": 0.25,
            "shoulder_press": 0.4, "lunge": 0.6
        }
        
        self.paused = False
        self.buttons = []
        self.hovered_button = None
        self.pulse_phase = 0
        self.rep_animation = 0
        self.mouse_x = 0; self.mouse_y = 0

    def speak(self, text, force=False):
        # If a coach is hired, prefix feedback with their persona
        if self.coach_name and "Starting" not in text and "Welcome" not in text:
            # Random chance to add coach flavor could be added here
            pass

        if force or (time.time() - self.last_speech > self.speech_cooldown):
            self.last_speech = time.time()
            threading.Thread(target=lambda: self._speak_thread(text), daemon=True).start()

    def _speak_thread(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except: pass

    def log_error(self, issue_name, voice_advice):
        if time.time() - self.last_error_time > 2.0:
            self.last_error_time = time.time()
            self.mistake_history.append(issue_name)
            self.form_score = max(0, self.form_score - 2)
            
            # Coach specific feedback style
            prefix = ""
            if self.coach_name:
                prefix = f"Coach {self.coach_name.split()[0]} says: "
            
            self.feedback = voice_advice
            self.speak(prefix + voice_advice, True)

    def calculate_angle(self, a, b, c):
        a = np.array(a); b = np.array(b); c = np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0: angle = 360 - angle
        return angle

    # --- EXERCISE LOGIC ---
    def check_squat(self, lm):
        angle = self.calculate_angle([lm[23].x,lm[23].y], [lm[25].x,lm[25].y], [lm[27].x,lm[27].y])
        if angle > 160: self.stage = "up"; self.feedback = "Ready"
        if angle < 90 and self.stage == "up":
            self.stage="down"; self.counter+=1; self.rep_animation=30; self.total_calories+=0.5
            self.speak(str(self.counter), True)
        elif angle < 130 and angle > 100 and self.stage == "up":
            self.log_error("Depth Limit", "Go Lower!")
        return angle

    def check_pushup(self, lm):
        angle = self.calculate_angle([lm[11].x,lm[11].y], [lm[13].x,lm[13].y], [lm[15].x,lm[15].y])
        if angle > 160: self.stage = "up"; self.feedback = "Ready"
        if angle < 90 and self.stage == "up":
            self.stage="down"; self.counter+=1; self.rep_animation=30; self.total_calories+=0.35
            self.speak(str(self.counter), True)
        elif angle < 130 and angle > 100 and self.stage == "up":
            self.log_error("Half Rep", "Chest Lower!")
        return angle

    def check_curl(self, lm):
        angle = self.calculate_angle([lm[11].x,lm[11].y], [lm[13].x,lm[13].y], [lm[15].x,lm[15].y])
        if angle > 160: self.stage = "down"; self.feedback = "Ready"
        if angle < 35 and self.stage == "down":
            self.stage="up"; self.counter+=1; self.rep_animation=30; self.total_calories+=0.25
            self.speak(str(self.counter), True)
        elif angle > 140 and self.stage == "up":
            self.log_error("Extension", "Full Extension!")
        return angle
        
    def check_press(self, lm):
        angle = self.calculate_angle([lm[11].x,lm[11].y], [lm[13].x,lm[13].y], [lm[15].x,lm[15].y])
        if angle < 90: self.stage = "down"; self.feedback = "Ready"
        if angle > 160 and self.stage == "down":
            self.stage="up"; self.counter+=1; self.rep_animation=30; self.total_calories+=0.4
            self.speak(str(self.counter), True)
        elif angle > 120 and angle < 150 and self.stage == "down":
            self.log_error("Range of Motion", "Push Higher!")
        return angle

    def check_lunge(self, lm):
        angle = self.calculate_angle([lm[23].x,lm[23].y], [lm[25].x,lm[25].y], [lm[27].x,lm[27].y])
        if angle > 160: self.stage = "up"; self.feedback = "Step Back"
        if angle < 100 and self.stage == "up":
            self.stage="down"; self.counter+=1; self.rep_animation=30; self.total_calories+=0.6
            self.speak(str(self.counter), True)
        elif angle < 130 and angle > 110 and self.stage == "up":
            self.log_error("Depth", "Drop Knee Lower!")
        return angle

    # --- UI DRAWING ---
    def create_rounded_rectangle(self, img, x, y, w, h, color, radius=15, alpha=0.9):
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x+w, y+h), color, -1)
        cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
    
    def draw_button(self, img, x, y, w, h, text, color=(102, 126, 234), is_hovered=False):
        if is_hovered: color = tuple([int(c * 1.2) if int(c * 1.2) <= 255 else 255 for c in color])
        self.create_rounded_rectangle(img, x, y, w, h, color, radius=10, alpha=0.85)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, 0.6, 2)[0]
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2
        cv2.putText(img, text, (text_x, text_y), font, 0.6, (255, 255, 255), 2)
        return (x, y, w, h)

    def draw_progress_bar(self, img, x, y, w, h, progress, color=(102, 226, 234)):
        cv2.rectangle(img, (x, y), (x+w, y+h), (50, 50, 50), -1)
        fill_w = int(w * progress / 100)
        cv2.rectangle(img, (x, y), (x+fill_w, y+h), color, -1)
        cv2.rectangle(img, (x, y), (x+w, y+h), (200, 200, 200), 2)
        text = f"{int(progress)}%"
        cv2.putText(img, text, (x + w + 10, y + h - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    def draw_stat_card(self, img, x, y, w, h, title, value, icon=""):
        self.create_rounded_rectangle(img, x, y, w, h, (40, 40, 50), radius=12, alpha=0.85)
        cv2.putText(img, icon, (x + 15, y + 35), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (102, 126, 234), 2)
        cv2.putText(img, title, (x + 15, y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        value_size = 1.2 if self.rep_animation > 0 else 1.0
        cv2.putText(img, str(value), (x + 15, y + 100), cv2.FONT_HERSHEY_SIMPLEX, value_size, (255, 255, 255), 2)

    def draw_interactive_ui(self, image):
        h, w = image.shape[:2]
        self.buttons = []
        self.pulse_phase += 0.1
        if self.rep_animation > 0: self.rep_animation -= 1
        
        
        self.create_rounded_rectangle(image, 0, 0, w, 80, (30, 30, 40), radius=0, alpha=0.9)
        title = "AI TRAINER PRO"
        if self.coach_name:
            title = f"LIVE SESSION: {self.coach_name.upper()}"
        
        cv2.putText(image, title, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (102, 126, 234), 3)
        
       
        if self.coach_name:
             self.create_rounded_rectangle(image, w-250, 90, 230, 40, (0, 0, 200), radius=5)
             cv2.putText(image, "🔴 LIVE COACHING", (w-240, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Exercise Buttons
        exercises = [
            ("Squats", "squat", (102, 226, 234)), ("Pushups", "pushup", (234, 102, 234)),
            ("Curls", "bicep_curl", (234, 202, 102)), ("Press", "shoulder_press", (234, 102, 166)),
            ("Lunge", "lunge", (102, 234, 166))
        ]
        
        btn_width = 110; btn_gap = 10
        total_width = len(exercises) * (btn_width + btn_gap)
        start_x = w - total_width - 20
        
        for i, (label, ex, col) in enumerate(exercises):
            is_active = self.exercise == ex
            is_hovered = self.hovered_button == f"ex_{i}"
            col = col if is_active else (70, 70, 80)
            btn = self.draw_button(image, start_x + i*(btn_width + btn_gap), 20, btn_width, 45, label, col, is_hovered)
            self.buttons.append((btn, f"ex_{i}", ex))
        
        # Stats Cards
        card_x = 20; card_y = 100; card_w = 200; card_h = 120
        self.draw_stat_card(image, card_x, card_y, card_w, card_h, "REPS", self.counter, "#")
        self.draw_stat_card(image, card_x, card_y + 140, card_w, card_h, "CALORIES", f"{self.total_calories:.1f}", "Kcal")
        
        if self.workout_start_time:
            elapsed = int(time.time() - self.workout_start_time)
            timer_text = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        else: timer_text = "00:00"
        self.draw_stat_card(image, card_x, card_y + 280, card_w, card_h, "TIME", timer_text, "Time")
        
        # Stage Indicator
        if not self.paused:
            stage_text = self.stage if self.stage else "START"
            stage_size = 3.0 if self.rep_animation > 0 else 2.0
            text_size = cv2.getTextSize(stage_text, cv2.FONT_HERSHEY_SIMPLEX, stage_size, 4)[0]
            text_x = (w - text_size[0]) // 2; text_y = h // 2
            cv2.putText(image, stage_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, stage_size, (255, 255, 255), 4)
        
        # Feedback Overlay
        if self.feedback and not self.paused:
            feedback_y = h - 180
            feedback_color = (0, 255, 0) if "Good" in self.feedback or "Ready" in self.feedback else (0, 200, 255)
            if "!" in self.feedback and "Perfect" not in self.feedback: feedback_color = (0, 100, 255)
            
            text_size = cv2.getTextSize(self.feedback, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            text_x = (w - text_size[0]) // 2
            self.create_rounded_rectangle(image, text_x - 20, feedback_y - 40, text_size[0] + 40, 60, (40, 40, 50), alpha=0.8)
            cv2.putText(image, self.feedback, (text_x, feedback_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, feedback_color, 3)

        # Bottom Controls
        btn_y = h - 100; c_width = 140; c_height = 50; gap = 20
        controls = [("Pause", "pause"), ("Reset", "reset"), ("Quit", "quit")]
        total_cw = len(controls) * (c_width + gap) - gap
        start_cx = (w - total_cw) // 2
        for i, (label, action) in enumerate(controls):
            col = (234, 102, 102) if action == "quit" else (102, 202, 234)
            is_hovered = self.hovered_button == f"control_{i}"
            btn = self.draw_button(image, start_cx + i*(c_width + gap), btn_y, c_width, c_height, label, col, is_hovered)
            self.buttons.append((btn, f"control_{i}", action))

        self.draw_progress_bar(image, w - 320, h - 50, 280, 20, max(0, self.form_score))

    def handle_click(self, x, y):
        for (bx, by, bw, bh), btn_id, action in self.buttons:
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if action == "quit": return True
                elif action == "pause": self.paused = not self.paused
                elif action == "reset": 
                    self.counter = 0; self.mistake_history = []; self.form_score = 100
                    self.workout_start_time = time.time()
                else: 
                    self.exercise = action; self.counter = 0; self.mistake_history = []; self.form_score = 100
                    self.speak(f"Starting {action}")
        return False

    def generate_report(self):
        if self.counter == 0: return "No reps completed."
        report = f"Great job! {self.counter} reps of {self.exercise}.\nScore: {self.form_score}%\n\n"
        if not self.mistake_history: report += "Perfect Form!"
        else:
            top_issue = Counter(self.mistake_history).most_common(1)[0][0]
            report += f"Main Issue: {top_issue}.\nCheck your form next time!"
        if self.coach_name:
            report += f"\n\n- Coach {self.coach_name} signed off."
        return report

    def save_session(self):
        duration = int(time.time() - self.workout_start_time)
        top_issue = Counter(self.mistake_history).most_common(1)[0][0] if self.mistake_history else "None"
        entry = {
            "username": self.username,
            "coach": self.coach_name if self.coach_name else "AI",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "exercise": self.exercise,
            "reps": self.counter,
            "calories": round(self.total_calories, 2),
            "duration": f"{duration//60}m {duration%60}s",
            "feedback": top_issue
        }
        history = []
        if os.path.exists('workout_history.json'):
            try:
                with open('workout_history.json', 'r') as f: history = json.load(f)
            except: pass
        history.append(entry)
        with open('workout_history.json', 'w') as f: json.dump(history, f, indent=2)

    def start(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened(): cap = cv2.VideoCapture(0)
        if not cap.isOpened(): cap = cv2.VideoCapture(1)
        if not cap or not cap.isOpened():
            messagebox.showerror("Error", "Camera not found!")
            return

        cap.set(3, 1280); cap.set(4, 720)
        cv2.namedWindow('AI Fitness Trainer Pro')
        
        def mouse_wrapper(event, x, y, flags, param):
            self.mouse_x = x; self.mouse_y = y
            if event == cv2.EVENT_MOUSEMOVE:
                self.hovered_button = None
                for (bx, by, bw, bh), bid, act in self.buttons:
                    if bx <= x <= bx + bw and by <= y <= by + bh:
                        self.hovered_button = bid; break
            if event == cv2.EVENT_LBUTTONDOWN:
                if self.handle_click(x, y): self.running = False 

        cv2.setMouseCallback('AI Fitness Trainer Pro', mouse_wrapper)
        
        self.workout_start_time = time.time()
        msg = f"Welcome {self.username}. "
        if self.coach_name: msg += f"Coach {self.coach_name} is online."
        self.speak(msg)
        self.running = True

        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            if not self.paused: results = self.pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if not self.paused and results.pose_landmarks:
                self.mp_drawing.draw_landmarks(image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                lm = results.pose_landmarks.landmark
                if self.exercise == "squat": self.check_squat(lm)
                elif self.exercise == "pushup": self.check_pushup(lm)
                elif self.exercise == "bicep_curl": self.check_curl(lm)
                elif self.exercise == "shoulder_press": self.check_press(lm)
                elif self.exercise == "lunge": self.check_lunge(lm)

            self.draw_interactive_ui(image)
            cv2.imshow('AI Fitness Trainer Pro', image)
            if cv2.waitKey(5) & 0xFF == ord('q'): break
            
        self.final_report = self.generate_report()
        self.save_session()
        cap.release()
        cv2.destroyAllWindows()
        return self.final_report


# ==========================================
# PART 2: THE DESKTOP APP (FRONTEND)
# ==========================================

class FitnessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Fitness Trainer - Login")
        self.root.geometry("400x500")
        self.root.configure(bg="#2c3e50")
        self.current_user = None
        self.selected_trainer = None
        self.show_login_screen()
        
        # MOCK TRAINER DATA
        self.trainers_data = [
            {"name": "Mike Tyson", "spec": "Strength & Power", "rate": "4.9", "price": "$50"},
            {"name": "Sarah Connor", "spec": "Cardio & Endurance", "rate": "4.8", "price": "$40"},
            {"name": "David Goggins", "spec": "Mental Toughness", "rate": "5.0", "price": "$100"},
            {"name": "Arnold S.", "spec": "Bodybuilding", "rate": "5.0", "price": "$200"},
        ]

    # --- SCREEN 1: LOGIN ---
    def show_login_screen(self):
        self.clear_window()
        self.root.geometry("400x500")
        tk.Label(self.root, text="💪 AI FITNESS", font=("Helvetica", 24, "bold"), bg="#2c3e50", fg="white").pack(pady=40)
        tk.Label(self.root, text="Username", bg="#2c3e50", fg="white").pack(pady=5)
        self.entry_user = tk.Entry(self.root, font=("Arial", 12)); self.entry_user.pack(pady=5, ipadx=20, ipady=5)
        tk.Label(self.root, text="Password", bg="#2c3e50", fg="white").pack(pady=5)
        self.entry_pass = tk.Entry(self.root, show="*", font=("Arial", 12)); self.entry_pass.pack(pady=5, ipadx=20, ipady=5)
        tk.Button(self.root, text="LOGIN", command=self.login, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), width=15).pack(pady=20)
        tk.Button(self.root, text="Create Account", command=self.register, bg="#2980b9", fg="white").pack()

    def login(self):
        user = self.entry_user.get(); pwd = self.entry_pass.get()
        if self.verify_user(user, pwd):
            self.current_user = user; self.show_dashboard()
        else: messagebox.showerror("Error", "Invalid Username or Password")

    def register(self):
        user = self.entry_user.get(); pwd = self.entry_pass.get()
        if not user or not pwd: messagebox.showwarning("Input", "Please fill all fields"); return
        users = self.load_users()
        if user in users: messagebox.showerror("Error", "User already exists")
        else:
            users[user] = pwd; self.save_users(users); messagebox.showinfo("Success", "Account created! Please Login.")

    def load_users(self):
        if os.path.exists("users.json"):
            with open("users.json", "r") as f: return json.load(f)
        return {}
    def save_users(self, data):
        with open("users.json", "w") as f: json.dump(data, f)
    def verify_user(self, user, pwd):
        users = self.load_users(); return user in users and users[user] == pwd

    # --- SCREEN 2: DASHBOARD ---
    def show_dashboard(self):
        self.clear_window(); self.root.geometry("900x700"); self.root.title(f"Dashboard - {self.current_user}")
        
        nav = tk.Frame(self.root, bg="#34495e", height=60); nav.pack(fill="x")
        tk.Label(nav, text=f"Welcome, {self.current_user}", bg="#34495e", fg="white", font=("Arial", 14)).pack(side="left", padx=20, pady=15)
        tk.Button(nav, text="Hire a Coach", command=self.show_marketplace, bg="#f39c12", fg="white").pack(side="right", padx=10)
        tk.Button(nav, text="Logout", command=self.show_login_screen, bg="#c0392b", fg="white").pack(side="right", padx=10)
        
        stats_frame = tk.Frame(self.root, bg="#2c3e50"); stats_frame.pack(fill="x", pady=20, padx=20)
        total_reps, total_cals = self.get_user_stats()
        self.create_stat_card(stats_frame, "Total Reps", str(total_reps), "#f39c12", 0)
        self.create_stat_card(stats_frame, "Calories Burnt", f"{total_cals:.1f}", "#e74c3c", 1)
        
        tk.Label(self.root, text="Recent Workouts", bg="#2c3e50", fg="white", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        
        table_frame = tk.Frame(self.root); table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        scroll = tk.Scrollbar(table_frame); scroll.pack(side="right", fill="y")
        cols = ("Date", "Coach", "Exercise", "Reps", "Feedback") 
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=scroll.set)
        
        for col in cols: 
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
            
        self.tree.pack(fill="both", expand=True); scroll.config(command=self.tree.yview)
        
        self.load_history_table()
        
        start_btn_text = "🚀 START TRAINING (AI ONLY)"
        if self.selected_trainer:
            start_btn_text = f"🔴 START LIVE SESSION WITH {self.selected_trainer['name'].upper()}"
            
        tk.Button(self.root, text=start_btn_text, command=self.launch_camera, bg="#27ae60", fg="white", font=("Arial", 16, "bold"), height=2).pack(fill="x", side="bottom")

    # --- SCREEN 3: COACH MARKETPLACE ---
    def show_marketplace(self):
        top = tk.Toplevel(self.root)
        top.title("Hire a Top Trainer")
        top.geometry("600x500")
        top.configure(bg="#ecf0f1")
        
        tk.Label(top, text="Select a Real-Time Coach", font=("Arial", 16, "bold"), bg="#ecf0f1").pack(pady=10)
        
        container = tk.Frame(top, bg="#ecf0f1")
        container.pack(fill="both", expand=True, padx=20)
        
        for i, t in enumerate(self.trainers_data):
            card = tk.Frame(container, bg="white", bd=1, relief="solid")
            card.pack(fill="x", pady=5, ipadx=10, ipady=10)
            
            tk.Label(card, text=t['name'], font=("Arial", 12, "bold"), bg="white").pack(side="left", padx=10)
            tk.Label(card, text=f"⭐ {t['rate']} | {t['spec']}", bg="white", fg="gray").pack(side="left", padx=10)
            
            def book(trainer=t):
                if messagebox.askyesno("Confirm Booking", f"Book session with {trainer['name']} for {trainer['price']}?"):
                    self.selected_trainer = trainer
                    messagebox.showinfo("Success", f"Booked {trainer['name']}! Start Training from Dashboard.")
                    top.destroy()
                    self.show_dashboard() # Refresh dashboard
            
            tk.Button(card, text=f"Book ({t['price']})", bg="#27ae60", fg="white", command=book).pack(side="right", padx=10)

    def create_stat_card(self, parent, title, value, color, col_idx):
        frame = tk.Frame(parent, bg=color, width=200, height=100)
        frame.grid(row=0, column=col_idx, padx=20, sticky="ew")
        frame.pack_propagate(False)
        tk.Label(frame, text=title, bg=color, fg="white", font=("Arial", 10)).pack(pady=(20, 5))
        tk.Label(frame, text=value, bg=color, fg="white", font=("Arial", 20, "bold")).pack()

    def get_user_stats(self):
        reps = 0; cals = 0
        if os.path.exists("workout_history.json"):
            with open("workout_history.json", "r") as f:
                data = json.load(f)
                for entry in data:
                    if entry.get("username") == self.current_user:
                        reps += entry.get("reps", 0); cals += entry.get("calories", 0)
        return reps, cals

    def load_history_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists("workout_history.json"):
            with open("workout_history.json", "r") as f:
                data = json.load(f)
                user_data = [d for d in data if d.get("username") == self.current_user]
                for entry in reversed(user_data):
                    self.tree.insert("", "end", values=(entry.get("date"), entry.get("coach", "AI"), entry.get("exercise").title(), entry.get("reps"), entry.get("feedback", "None")))

    def launch_camera(self):
        self.root.withdraw()
        c_name = self.selected_trainer['name'] if self.selected_trainer else None
        trainer = InteractiveFitnessTrainer(self.current_user, c_name)
        report = trainer.start() 
        self.root.deiconify()
        if report: messagebox.showinfo("Workout Summary", report)
        self.selected_trainer = None # Reset booking
        self.show_dashboard()

    def clear_window(self):
        for widget in self.root.winfo_children(): widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FitnessApp(root)
    root.mainloop()