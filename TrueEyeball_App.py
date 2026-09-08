import customtkinter as ctk
from PIL import Image
import threading
import queue
import cv2
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TrueEyeballDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("TrueEyeball AI Platform")
        self.geometry("1400x900")
        
        # Threading Video Loop Exchange
        self.frame_queue = queue.Queue(maxsize=30)
        self.is_running = True
        
        self._build_ui()
        self._start_backend()
        
    def _build_ui(self):
        # Master grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left Navigation Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        logo_label = ctk.CTkLabel(self.sidebar_frame, text="TrueEyeball AI", font=ctk.CTkFont(size=24, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Live Dashboard")
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_analytics = ctk.CTkButton(self.sidebar_frame, text="Analytics Hub")
        self.btn_analytics.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Hardware Settings")
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_wizard = ctk.CTkButton(self.sidebar_frame, text="Run Calibration Wizard", fg_color="green", hover_color="darkgreen", command=self.open_wizard)
        self.btn_wizard.grid(row=4, column=0, padx=20, pady=10)
        
        # Appearance Toggle
        appearance_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:")
        appearance_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_option = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                   command=self.change_appearance)
        self.appearance_option.grid(row=7, column=0, padx=20, pady=(10, 20))
        
        # Main Display
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.main_frame.grid_columnconfigure(0, weight=3) # Video takes 75%
        self.main_frame.grid_columnconfigure(1, weight=1) # Side stats takes 25%
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Video Canvas
        self.video_canvas = ctk.CTkLabel(self.main_frame, text="Waiting for AI Engine...", fg_color="black")
        self.video_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Stats Widget Panel Right
        self.stats_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="System Health Monitoring")
        self.stats_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.lbl_fps = ctk.CTkLabel(self.stats_frame, text="FPS: --", font=ctk.CTkFont(size=14))
        self.lbl_fps.pack(anchor="w", pady=5, padx=10)
        
        self.lbl_auth = ctk.CTkLabel(self.stats_frame, text="Auth Status: LOCKED", font=ctk.CTkFont(size=14))
        self.lbl_auth.pack(anchor="w", pady=5, padx=10)
        
        self.lbl_context = ctk.CTkLabel(self.stats_frame, text="Context Mode: Scanning...", font=ctk.CTkFont(size=14))
        self.lbl_context.pack(anchor="w", pady=5, padx=10)

    def change_appearance(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        
    def open_wizard(self):
        from modules.ui.calibration_wizard import CalibrationWizard
        wizard = CalibrationWizard(self)
        wizard.grab_set() # Focus lock

    def _start_backend(self):
        from core_backend import start_ai_loop
        self.ai_thread = threading.Thread(target=start_ai_loop, args=(self.frame_queue, lambda: self.is_running), daemon=True)
        self.ai_thread.start()
        
        self._update_video()
        
    def _update_video(self):
        if not self.is_running: return
        
        try:
            # Drain queue smoothly, rendering the MOST RECENT frame only if it lags
            best_frame = None
            stats = None
            while not self.frame_queue.empty():
                payload = self.frame_queue.get_nowait()
                best_frame = payload["frame"]
                stats = payload["stats"]
                
            if best_frame is not None:
                # Convert BGR (OpenCV) -> RGB (Pillow) -> CTkImage
                rgb_frame = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                
                # Dynamic resize mapping
                w, h = self.video_canvas.winfo_width(), self.video_canvas.winfo_height()
                if w > 10 and h > 10:
                    ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(w, h))
                    self.video_canvas.configure(image=ctk_image, text="")
                    self.video_canvas._image = ctk_image # Prevent GC
                    
            if stats is not None:
                self.lbl_fps.configure(text=f"Engine Latency: {stats.get('latency', 0):.1f} ms")
                self.lbl_auth.configure(text=f"Auth Status: {stats.get('auth_state', 'LOCKED')}")
                context_str = stats.get('context_mode', 'Unknown')
                self.lbl_context.configure(text=f"Focus: {context_str}")
        except Exception:
            pass
            
        self.after(30, self._update_video) # Refresh at ~33 FPS UI overlay

    def on_closing(self):
        self.is_running = False
        self.destroy()

if __name__ == "__main__":
    app = TrueEyeballDashboard()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
