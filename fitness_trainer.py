"""
Quick launcher for AI Fitness Trainer
Run this directly to start the trainer without the web app
"""

import subprocess
import sys
import os

def launch_trainer():
    """Launch the fitness trainer application"""
    try:
        # Check if fitness_trainer.py exists
        if not os.path.exists('fitness_trainer.py'):
            print("❌ Error: fitness_trainer.py not found!")
            print("Make sure you're in the correct directory (D:\\AI_Trainer)")
            input("Press Enter to exit...")
            return
        
        print("🚀 Launching AI Fitness Trainer...")
        print("📹 Make sure your camera is connected!")
        print("\n" + "="*50)
        
        # Get Python executable
        python_exe = sys.executable
        
        # Launch the trainer
        if os.name == 'nt':  # Windows
            subprocess.run([python_exe, 'fitness_trainer.py'])
        else:  # Linux/Mac
            subprocess.run([python_exe, 'fitness_trainer.py'])
        
    except KeyboardInterrupt:
        print("\n\n✓ Trainer closed by user")
    except Exception as e:
        print(f"\n❌ Error launching trainer: {str(e)}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    launch_trainer()