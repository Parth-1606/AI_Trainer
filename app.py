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
        
        # Premium Color Palette (BGR)
        self.colors = {
            "bg": (16, 11, 10),
            "card_bg": (25, 20, 18),
            "cyan": (255, 242, 0),
            "pink": (247, 0, 255),
            "green": (136, 255, 0),
            "white": (255, 255, 255),
            "text_dim": (158, 148, 139)
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
        if radius > 0:
            cv2.rectangle(overlay, (x + radius, y), (x + w - radius, y + h), color, -1)
            cv2.rectangle(overlay, (x, y + radius), (x + w, y + h - radius), color, -1)
            cv2.circle(overlay, (x + radius, y + radius), radius, color, -1, cv2.LINE_AA)
            cv2.circle(overlay, (x + w - radius, y + radius), radius, color, -1, cv2.LINE_AA)
            cv2.circle(overlay, (x + radius, y + h - radius), radius, color, -1, cv2.LINE_AA)
            cv2.circle(overlay, (x + w - radius, y + h - radius), radius, color, -1, cv2.LINE_AA)
        else:
            cv2.rectangle(overlay, (x, y), (x+w, y+h), color, -1)
        cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
    
    def draw_button(self, img, x, y, w, h, text, color=(102, 126, 234), is_hovered=False):
        if is_hovered: color = tuple([int(c * 1.2) if int(c * 1.2) <= 255 else 255 for c in color])
        self.create_rounded_rectangle(img, x, y, w, h, color, radius=8, alpha=0.85)
        font = cv2.FONT_HERSHEY_DUPLEX
        text_size = cv2.getTextSize(text, font, 0.5, 1)[0]
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2
        cv2.putText(img, text, (text_x, text_y), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return (x, y, w, h)

    def draw_progress_bar(self, img, x, y, w, h, progress, color=(102, 226, 234)):
        self.create_rounded_rectangle(img, x, y, w, h, (40, 40, 40), radius=h//2, alpha=0.8)
        fill_w = max(h, int(w * progress / 100))
        if progress > 0:
            self.create_rounded_rectangle(img, x, y, fill_w, h, color, radius=h//2, alpha=1.0)
        cv2.rectangle(img, (x, y), (x+w, y+h), (200, 200, 200), 1, cv2.LINE_AA)
        text = f"{int(progress)}%"
        cv2.putText(img, text, (x + w + 10, y + h - 2), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    def draw_stat_card(self, img, x, y, w, h, title, value, icon="", color=None):
        if color is None: color = self.colors["cyan"]
        self.create_rounded_rectangle(img, x, y, w, h, self.colors["bg"], radius=12, alpha=0.8)
        cv2.rectangle(img, (x, y), (x+w, y+h), (60, 60, 60), 1, cv2.LINE_AA)
        cv2.rectangle(img, (x, y+15), (x+4, y+h-15), color, -1)
        cv2.putText(img, title, (x + 15, y + 25), cv2.FONT_HERSHEY_DUPLEX, 0.4, self.colors["text_dim"], 1, cv2.LINE_AA)
        val_str = str(value)
        font_scale = 1.0 if self.rep_animation > 0 else 0.8
        cv2.putText(img, val_str, (x + 15, y + 60), cv2.FONT_HERSHEY_DUPLEX, font_scale, self.colors["white"], 1, cv2.LINE_AA)

    def draw_circular_progress(self, img, center, radius, progress, total, label="REPS"):
        x, y = center
        cv2.circle(img, center, radius, (40, 40, 40), 8, cv2.LINE_AA)
        angle = (progress / total) * 360 if total > 0 else 0
        cv2.ellipse(img, center, (radius, radius), -90, 0, angle, self.colors["cyan"], 8, cv2.LINE_AA)
        val_text = f"{progress}"
        text_size = cv2.getTextSize(val_text, cv2.FONT_HERSHEY_DUPLEX, 1.2, 2)[0]
        cv2.putText(img, val_text, (x - text_size[0]//2, y + text_size[1]//2 + 2), cv2.FONT_HERSHEY_DUPLEX, 1.2, self.colors["white"], 2, cv2.LINE_AA)
        label_text = f"{progress}/{total}"
        lbl_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_DUPLEX, 0.4, 1)[0]
        cv2.putText(img, label_text, (x - lbl_size[0]//2, y + radius + 25), cv2.FONT_HERSHEY_DUPLEX, 0.4, self.colors["text_dim"], 1, cv2.LINE_AA)

    def draw_interactive_ui(self, image):
        h, w = image.shape[:2]
        self.buttons = []
        self.pulse_phase += 0.1
        if self.rep_animation > 0: self.rep_animation -= 1
        
        # Top Bar
        self.create_rounded_rectangle(image, 20, 20, 360, 45, self.colors["bg"], radius=15, alpha=0.85)
        cv2.putText(image, "AI TRAINER // PRO VISION", (40, 48), cv2.FONT_HERSHEY_DUPLEX, 0.6, self.colors["cyan"], 1, cv2.LINE_AA)
        
        # Exercise Selector (Top Right)
        exercises = [("SQUAT", "squat"), ("PUSHUP", "pushup"), ("CURL", "bicep_curl"), ("PRESS", "shoulder_press")]
        btn_w = 85; gap = 12
        for i, (label, ex) in enumerate(exercises):
            is_active = self.exercise == ex
            col = self.colors["cyan"] if is_active else (60, 60, 60)
            is_hovered = self.hovered_button == f"ex_{i}"
            btn = self.draw_button(image, w - (len(exercises)-i)*(btn_w+gap) - 20, 20, btn_w, 45, label, col, is_hovered)
            self.buttons.append((btn, f"ex_{i}", ex))

        # Circular Rep Counter (Top Center-ish)
        self.draw_circular_progress(image, (w - 150, 150), 55, self.counter, 15)

        # Stats Sidebar (Right)
        side_x = w - 240
        self.draw_stat_card(image, side_x, 240, 220, 80, "CALORIES", f"{self.total_calories:.1f} kcal", color=self.colors["pink"])
        self.draw_stat_card(image, side_x, 340, 220, 80, "FORM SCORE", f"{self.form_score}%", color=self.colors["green"])
        
        # Biomechanics Feedback (Bottom Left)
        if self.feedback:
            self.create_rounded_rectangle(image, 30, h - 140, 380, 60, self.colors["bg"], radius=12, alpha=0.85)
            cv2.putText(image, "BIOMECHANICS FEEDBACK:", (45, h - 115), cv2.FONT_HERSHEY_DUPLEX, 0.4, self.colors["cyan"], 1, cv2.LINE_AA)
            cv2.putText(image, self.feedback.upper(), (45, h - 90), cv2.FONT_HERSHEY_DUPLEX, 0.6, self.colors["white"], 1, cv2.LINE_AA)

        # Bottom Controls
        ctrl_y = h - 65; cw = 110; ch = 45; cgap = 15
        controls = [("PAUSE", "pause"), ("RESET", "reset"), ("QUIT", "quit")]
        for i, (label, act) in enumerate(controls):
            col = (50, 50, 200) if act == "quit" else (90, 90, 90)
            is_hovered = self.hovered_button == f"ctrl_{i}"
            btn = self.draw_button(image, 30 + i*(cw+cgap), ctrl_y, cw, ch, label, col, is_hovered)
            self.buttons.append((btn, f"ctrl_{i}", act))

        self.draw_progress_bar(image, w - 320, h - 50, 280, 15, max(0, self.form_score), color=self.colors["green"])

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
                # Custom Neon Skeleton
                landmark_drawing_spec = self.mp_drawing.DrawingSpec(color=(255, 0, 255), thickness=2, circle_radius=3)
                connection_drawing_spec = self.mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2)
                
                self.mp_drawing.draw_landmarks(
                    image, 
                    results.pose_landmarks, 
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec,
                    connection_drawing_spec
                )
                
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
        self.root.title("AI TRAINER // CORE INITIALIZATION")
        self.root.geometry("400x600")
        self.root.configure(bg="#0a0b10")
        self.current_user = None
        self.selected_trainer = None
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", 
            background="#161b22", 
            foreground="white", 
            fieldbackground="#161b22",
            borderwidth=0)
        self.style.map("Treeview", background=[('selected', '#00f2ff')])
        
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
        self.root.geometry("400x600")
        
        # Logo Area
        tk.Label(self.root, text="A I   T R A I N E R", font=("Helvetica", 20, "bold"), bg="#0a0b10", fg="#00f2ff").pack(pady=(60, 10))
        tk.Label(self.root, text="PRO VISION SYSTEM", font=("Helvetica", 8), bg="#0a0b10", fg="#8b949e").pack(pady=(0, 40))
        
        # Inputs
        container = tk.Frame(self.root, bg="#0a0b10")
        container.pack(pady=10, padx=40, fill="x")
        
        tk.Label(container, text="USER_IDENTITY", bg="#0a0b10", fg="#8b949e", font=("Arial", 8, "bold")).pack(anchor="w")
        self.entry_user = tk.Entry(self.root, font=("Arial", 12), bg="#161b22", fg="white", insertbackground="white", bd=0); 
        self.entry_user.pack(pady=(5, 20), padx=40, ipady=10, fill="x")
        
        tk.Label(container, text="ACCESS_KEY", bg="#0a0b10", fg="#8b949e", font=("Arial", 8, "bold")).pack(anchor="w")
        self.entry_pass = tk.Entry(self.root, show="*", font=("Arial", 12), bg="#161b22", fg="white", insertbackground="white", bd=0); 
        self.entry_pass.pack(pady=(5, 30), padx=40, ipady=10, fill="x")
        
        tk.Button(self.root, text="INITIALIZE", command=self.login, bg="#00f2ff", fg="#0a0b10", font=("Arial", 12, "bold"), bd=0, cursor="hand2").pack(pady=10, padx=40, fill="x", ipady=10)
        tk.Button(self.root, text="CREATE NEW IDENTITY", command=self.register, bg="#0a0b10", fg="#ff00f7", font=("Arial", 10), bd=0, cursor="hand2").pack(pady=10)

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
        self.clear_window(); self.root.geometry("1000x750"); self.root.title(f"COMMAND CENTER // {self.current_user}")
        self.root.configure(bg="#0a0b10")
        
        # Navigation Bar
        nav = tk.Frame(self.root, bg="#161b22", height=70); nav.pack(fill="x")
        tk.Label(nav, text=f"OPERATOR: {self.current_user}", bg="#161b22", fg="#00f2ff", font=("Helvetica", 14, "bold")).pack(side="left", padx=30, pady=20)
        tk.Button(nav, text="LOGOUT", command=self.show_login_screen, bg="#161b22", fg="#ff4d4d", bd=0, padx=20).pack(side="right", padx=20)
        tk.Button(nav, text="HIRE COACH", command=self.show_marketplace, bg="#00f2ff", fg="#0a0b10", font=("Arial", 9, "bold"), bd=0, padx=15).pack(side="right", padx=10)
        
        # Stats Cards
        stats_frame = tk.Frame(self.root, bg="#0a0b10"); stats_frame.pack(fill="x", pady=(30, 10), padx=30)
        total_reps, total_cals = self.get_user_stats()
        self.create_stat_card(stats_frame, "AGGREGATE REPS", str(total_reps), "#00f2ff", 0)
        self.create_stat_card(stats_frame, "CALORIC BURN", f"{total_cals:.1f}", "#ff00f7", 1)
        
        # Start Button
        btn_text = ">>> INITIALIZE MISSION (AI CORE) <<<"
        if self.selected_trainer:
            btn_text = f">>> LIVE SESSION: {self.selected_trainer['name'].upper()} <<<"
        tk.Button(self.root, text=btn_text, command=self.launch_camera, bg="#00f2ff", fg="#0a0b10", font=("Helvetica", 14, "bold"), height=2, bd=0, cursor="hand2").pack(fill="x", padx=30, pady=15)

        # Mission Logs Table
        tk.Label(self.root, text="RECENT MISSION LOGS", bg="#0a0b10", fg="#8b949e", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=30, pady=(10, 5))
        
        table_frame = tk.Frame(self.root, bg="#161b22", bd=0); table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        scroll = tk.Scrollbar(table_frame); scroll.pack(side="right", fill="y")
        cols = ("Date", "Coach", "Exercise", "Reps", "Feedback") 
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=scroll.set)
        for col in cols: 
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill="both", expand=True); scroll.config(command=self.tree.yview)
        
        # Now load data AFTER tree exists
        self.load_history_table()

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
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == '--user':
        username = sys.argv[2]
        trainer = InteractiveFitnessTrainer(username)
        trainer.start()
    else:
        root = tk.Tk()
        app = FitnessApp(root)
        root.mainloop()