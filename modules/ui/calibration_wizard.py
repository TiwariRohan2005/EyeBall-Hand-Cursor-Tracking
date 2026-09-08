import customtkinter as ctk
import threading
import time
from modules.calibration.calibration_engine import CalibrationEngine

class CalibrationWizard(ctk.CTkToplevel):
    """
    Modern Wizard overlay replacing the terminal-based 'register.py'.
    Guides the user visually through Registration -> Blink Capture -> Setup.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("TrueEyeball Calibration & Registration Wizard")
        self.geometry("600x500")
        self.attributes('-topmost', True)
        
        self.current_step = 0
        self.steps = [
            ("Welcome to TrueEyeball", "Let's align your physical features to the AI. First, what should we call you?"),
            ("Facial Enrollment", "The system needs to securely encrypt your unique facial geometry."),
            ("Kinematics Calibration", "Stare naturally, blink a few times, and test glancing to allow the Adaptive Engine to baseline your hardware.")
        ]
        
        self.username_var = ctk.StringVar(value="")
        
        self._build_ui()
        self.update_step()

    def _build_ui(self):
        # Progress Bar Header
        self.progress = ctk.CTkProgressBar(self, width=500)
        self.progress.pack(pady=(20, 10))
        self.progress.set(0.1)
        
        # Central Action Frame
        self.content_frame = ctk.CTkFrame(self, width=500, height=300)
        self.content_frame.pack_propagate(False)
        self.content_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(self.content_frame, text="", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(pady=(30, 10))
        
        self.desc_label = ctk.CTkLabel(self.content_frame, text="", wraplength=400, font=ctk.CTkFont(size=14))
        self.desc_label.pack(pady=10)
        
        # Dynamic Widget Area
        self.widget_area = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.widget_area.pack(pady=20, fill="x")
        
        # Controls Frame
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(pady=(0, 20), fill="x", side="bottom")
        
        self.btn_back = ctk.CTkButton(self.controls_frame, text="< Back", command=self.prev_step, width=100)
        self.btn_back.pack(side="left", padx=20)
        
        self.btn_next = ctk.CTkButton(self.controls_frame, text="Next >", command=self.next_step, width=100)
        self.btn_next.pack(side="right", padx=20)

    def _clear_widgets(self):
        for widget in self.widget_area.winfo_children():
            widget.destroy()

    def update_step(self):
        t, d = self.steps[self.current_step]
        self.title_label.configure(text=t)
        self.desc_label.configure(text=d)
        
        self.progress.set( (self.current_step + 1) / len(self.steps) )
        
        self.btn_back.configure(state="normal" if self.current_step > 0 else "disabled")
        
        if self.current_step == len(self.steps) - 1:
            self.btn_next.configure(text="Launch Setup")
        else:
            self.btn_next.configure(text="Next >")
            
        self._build_step_content()

    def _build_step_content(self):
        self._clear_widgets()
        
        if self.current_step == 0:
            entry = ctk.CTkEntry(self.widget_area, textvariable=self.username_var, placeholder_text="Enter your Username", width=250)
            entry.pack(pady=10)
            
        elif self.current_step == 1:
            lbl = ctk.CTkLabel(self.widget_area, text="This step requires exclusive webcam access.\nIf the Dashboard is running, it will pause.", text_color="yellow")
            lbl.pack(pady=10)
            
        elif self.current_step == 2:
            lbl = ctk.CTkLabel(self.widget_area, text="Make sure your face is well-lit.\nPress 'Launch Setup' when ready.", text_color="cyan")
            lbl.pack(pady=10)

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step()

    def next_step(self):
        if self.current_step == 0 and not self.username_var.get().strip():
             return # Enforce requirement
             
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_step()
        else:
            # Execute physical backend hook!
            self.btn_next.configure(state="disabled", text="Calibrating...")
            self.update()
            self._trigger_backend_calibration()
            
    def _trigger_backend_calibration(self):
        # Fire off blocking visual calibration inside thread
        user = self.username_var.get().strip()
        
        def run_cal():
            try:
                from modules.auth import AuthManager
                auth = AuthManager()
                auth.enroll_user(user) # this pops a native cv2 window which is fine for calibration bounds
                
                engine = CalibrationEngine(user)
                engine.run_calibration_process()
                
                self.after(0, self._finish)
            except Exception as e:
                print(f"Calibration Wizard Error: {e}")
                self.after(0, lambda: self.btn_next.configure(state="normal", text="Retry calibration"))
                
        t = threading.Thread(target=run_cal, daemon=True)
        t.start()
        
    def _finish(self):
        self.destroy()
