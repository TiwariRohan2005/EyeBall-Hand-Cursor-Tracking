import cv2
import sys
import json
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image

from modules.eye_tracker import EyeTracker
from modules.auth import AuthManager
from modules.calibration import CalibrationEngine
from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RegistrationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Management System - User Registration")
        self.geometry("900x850") # Larger for full flow
        
        self.db_mgr = DatabaseManager()
        self.db_mgr.init_db()
        self.repo = LibraryRepository(self.db_mgr)
        
        self.camera_running = False
        self.cap = None
        self.eye_tracker = None
        self.calib_engine = None
        self.auth_manager = None
        
        self.biometric_success = False
        self.temp_calib_payload = None
        
        # Handle X close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self._build_ui()
        self._refresh_capacity()

    def _refresh_capacity(self):
        counts = self.repo.get_role_counts()
        self.owner_count = counts.get("OWNER", 0)
        self.staff_count = counts.get("STAFF", 0)
        
        self.lbl_owner_cap.configure(text=f"Owner: {self.owner_count} / 1", text_color="red" if self.owner_count >= 1 else "white")
        self.lbl_staff_cap.configure(text=f"Staff: {self.staff_count} / 10", text_color="red" if self.staff_count >= 10 else "white")
        avail = 10 - self.staff_count
        self.lbl_avail_cap.configure(text=f"Available Staff slots: {avail}")
        
        # Adjust roles dynamically
        if self.owner_count >= 1:
            self.rb_owner.configure(state="disabled")
            if self.role_var.get() == "OWNER":
                self.role_var.set("STAFF")
        else:
            self.rb_owner.configure(state="normal")
            
        if self.staff_count >= 10:
            self.rb_staff.configure(state="disabled")
            
    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=10)
        ctk.CTkLabel(hdr, text="AI MANAGEMENT SYSTEM", font=ctk.CTkFont(size=24, weight="bold")).pack()
        ctk.CTkLabel(hdr, text="USER REGISTRATION", font=ctk.CTkFont(size=18)).pack()
        
        layout = ctk.CTkFrame(self, fg_color="transparent")
        layout.pack(fill="both", expand=True, padx=20, pady=10)
        
        # LEFT COLUMN (Info)
        left = ctk.CTkFrame(layout, width=300)
        left.pack(side="left", fill="y", padx=10)
        
        # Capacity
        ctk.CTkLabel(left, text="USER CAPACITY", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.lbl_owner_cap = ctk.CTkLabel(left, text="")
        self.lbl_owner_cap.pack()
        self.lbl_staff_cap = ctk.CTkLabel(left, text="")
        self.lbl_staff_cap.pack()
        self.lbl_avail_cap = ctk.CTkLabel(left, text="")
        self.lbl_avail_cap.pack(pady=(0, 10))
        
        ctk.CTkLabel(left, text="-"*40).pack()
        
        # Form
        ctk.CTkLabel(left, text="USER INFORMATION", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(left, text="Display Name:").pack(anchor="w", padx=20)
        self.entry_name = ctk.CTkEntry(left, placeholder_text="e.g. John Doe")
        self.entry_name.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(left, text="Username (Login ID):").pack(anchor="w", padx=20)
        self.entry_username = ctk.CTkEntry(left, placeholder_text="e.g. jdoe")
        self.entry_username.pack(fill="x", padx=20, pady=(0, 10))
        
        self.role_var = tk.StringVar(value="STAFF")
        ctk.CTkLabel(left, text="Role:").pack(anchor="w", padx=20)
        
        rb_frame = ctk.CTkFrame(left, fg_color="transparent")
        rb_frame.pack(fill="x", padx=20, pady=5)
        self.rb_owner = ctk.CTkRadioButton(rb_frame, text="OWNER", variable=self.role_var, value="OWNER")
        self.rb_owner.pack(side="left", padx=5)
        self.rb_staff = ctk.CTkRadioButton(rb_frame, text="STAFF", variable=self.role_var, value="STAFF")
        self.rb_staff.pack(side="left", padx=5)

        ctk.CTkLabel(left, text="-"*40).pack(pady=10)
        self.lbl_status = ctk.CTkLabel(left, text="Status: Ready", text_color="yellow")
        self.lbl_status.pack(pady=5)
        
        # RIGHT COLUMN (Bio)
        right = ctk.CTkFrame(layout)
        right.pack(side="right", fill="both", expand=True, padx=10)
        
        ctk.CTkLabel(right, text="BIOMETRIC ENROLLMENT", font=ctk.CTkFont(weight="bold", size=16)).pack(pady=10)
        
        self.video_label = ctk.CTkLabel(right, text="[ LIVE CAMERA PREVIEW ]", width=500, height=350, fg_color="gray30")
        self.video_label.pack(pady=10)
        
        self.lbl_face_status = ctk.CTkLabel(right, text="Face status: Waiting for execution...", font=ctk.CTkFont(size=14))
        self.lbl_face_status.pack(pady=5)
        
        self.lbl_enroll_status = ctk.CTkLabel(right, text="Enrollment: Not started", font=ctk.CTkFont(size=14))
        self.lbl_enroll_status.pack(pady=5)
        
        # Actions
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.pack(fill="x", pady=20)
        
        self.btn_start = ctk.CTkButton(actions, text="Start Face Enrollment", command=self.start_enrollment)
        self.btn_start.pack(pady=5, fill="x", padx=50)
        
        self.btn_complete = ctk.CTkButton(actions, text="Complete Registration", command=self.complete_registration, state="disabled", fg_color="#27AE60")
        self.btn_complete.pack(pady=5, fill="x", padx=50)
        
        self.btn_cancel = ctk.CTkButton(actions, text="Cancel", fg_color="#E74C3C", command=self.on_closing)
        self.btn_cancel.pack(pady=5, fill="x", padx=50)

    def start_enrollment(self):
        # Validation checks
        name = self.entry_name.get().strip()
        username = self.entry_username.get().strip()
        role = self.role_var.get()
        
        if not name:
            messagebox.showerror("Error", "Please enter a display name.")
            return
        if not username:
            messagebox.showerror("Error", "Please enter a username.")
            return
        if not role:
            messagebox.showerror("Error", "Please select a role.")
            return
            
        counts = self.repo.get_role_counts()
        if role == "OWNER" and counts.get("OWNER", 0) >= 1:
            messagebox.showerror("Limit Reached", "Owner account already exists. Only one Owner is permitted.")
            return
        if role == "STAFF" and counts.get("STAFF", 0) >= 10:
            messagebox.showerror("Limit Reached", "Staff limit reached. A maximum of 10 Staff members is allowed.")
            return
            
        if self.repo.get_user_by_username(username):
            messagebox.showerror("Error", "Username already exists in DB.")
            return
            
        # Freeze inputs
        self.entry_name.configure(state="disabled")
        self.entry_username.configure(state="disabled")
        self.rb_owner.configure(state="disabled")
        self.rb_staff.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        
        self.lbl_status.configure(text="Status: Enrolling...", text_color="yellow")
        self.lbl_face_status.configure(text="Face status: Searching for face...")
        
        self.biometric_success = False
        
        # Start Engine
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Camera unavailable. Please check camera connection.")
            self._reset_ui_state()
            return
            
        self.eye_tracker = EyeTracker()
        self.calib_engine = CalibrationEngine()
        self.auth_manager = AuthManager(mode="ENROLLING", target_user_id=username)
        
        self.camera_running = True
        self.update_gui()

    def update_gui(self):
        if not self.camera_running:
            return
            
        ret, frame = self.cap.read()
        if not ret:
            self.after(10, self.update_gui)
            return
            
        frame = cv2.flip(frame, 1)
        
        # AI Processing
        frame_proc, eye_status, face_landmarks = self.eye_tracker.process(frame.copy())
        
        if face_landmarks:
            self.lbl_face_status.configure(text="Face status: Face detected. Hold still...", text_color="green")
            h, w, _ = frame.shape
            self.calib_engine.process_frame(frame, face_landmarks, h, w)
        else:
            self.lbl_face_status.configure(text="Face status: No face detected. Please position your face.", text_color="red")
            
        auth_state, current_uid_ignore, progress = self.auth_manager.process_face(face_landmarks)
        
        if auth_state == "ENROLLMENT_COMPLETE":
            self.lbl_enroll_status.configure(text="Enrollment: ✓ Complete", text_color="green")
            self.btn_complete.configure(state="normal")
            
            self.temp_calib_payload = self.calib_engine.finalize_calibration()
            self.biometric_success = True
            
            # Freeze camera successfully
            self._stop_camera()
            self.lbl_status.configure(text="Status: Ready to create account", text_color="green")
            self.video_label.configure(text="[ BIOMETRIC CAPTURED ]")
            return
            
        elif auth_state == "ENROLLING":
            self.lbl_enroll_status.configure(text=f"Capturing biometric sample... ({progress:0.0%})")
            
        # Draw bounding boxes etc provided by eye_tracker, convert to Tk Image
        frame_rgb = cv2.cvtColor(frame_proc, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(frame_rgb)
        ctk_img = ctk.CTkImage(light_image=im_pil, dark_image=im_pil, size=(500, 350))
        self.video_label.configure(image=ctk_img, text="")
        
        # Loop
        self.after(15, self.update_gui)

    def complete_registration(self):
        if not self.biometric_success:
            return
            
        username = self.entry_username.get().strip()
        role = self.role_var.get()
        name = self.entry_name.get().strip()
        
        # Atomic Final Check
        counts = self.repo.get_role_counts()
        if role == "OWNER" and counts.get("OWNER", 0) >= 1:
            messagebox.showerror("Limit Reached", "Owner account already exists. Only one Owner is permitted.")
            self._reset_ui_state()
            return
        if role == "STAFF" and counts.get("STAFF", 0) >= 10:
            messagebox.showerror("Limit Reached", "Staff limit reached. A maximum of 10 Staff members is allowed.")
            self._reset_ui_state()
            return
            
        try:
            self.repo.add_user(username=username, role=role, display_name=name)
            
            with open(f".user_{username}_learning.json", "w") as f:
                json.dump(self.temp_calib_payload, f)
                
            msg = f"REGISTRATION SUCCESSFUL\n\nName: {name}\nUsername: {username}\nRole: {role}\nBiometric enrollment: SUCCESS\nAccount status: ACTIVE"
            messagebox.showinfo("Success", msg)
            
            self.destroy()
            
        except PermissionError as e:
            messagebox.showerror("Limit Reached", str(e))
            self._reset_ui_state()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete registration: {e}")
            self._reset_ui_state()

    def _reset_ui_state(self):
        self._stop_camera()
        self.biometric_success = False
        self.temp_calib_payload = None
        
        self.entry_name.configure(state="normal")
        self.entry_username.configure(state="normal")
        
        self.btn_start.configure(state="normal")
        self.btn_complete.configure(state="disabled")
        
        self.video_label.configure(image=None, text="[ LIVE CAMERA PREVIEW ]")
        self.lbl_face_status.configure(text="Face status: Waiting for face...")
        self.lbl_enroll_status.configure(text="Enrollment: Not started")
        
        self._refresh_capacity()

    def _stop_camera(self):
        self.camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.eye_tracker and hasattr(self.eye_tracker, 'face_mesh'):
            self.eye_tracker.face_mesh.close()
            
    def on_closing(self):
        self._stop_camera()
        self.destroy()

if __name__ == "__main__":
    app = RegistrationApp()
    app.mainloop()
