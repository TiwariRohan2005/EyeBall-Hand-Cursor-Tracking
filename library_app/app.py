import customtkinter as ctk
from PIL import Image
import cv2
import sys
import os
import time
from tkinter import messagebox

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from library_app.models import LibraryModel, NotesModel
from library_app.gestures import LibraryGestureEngine
from modules.auth.auth_manager import AuthManager
from modules.eye_tracker import EyeTracker
from library_app.ui.dialogs import BookDetailsDialog, BookFormDialog
from library_app.permissions import PermissionManager, Permission
from library_app.reports.report_service import ReportService
from library_app.commands.command_registry import CommandRegistry
from library_app.commands.library_commands import register_library_commands
from library_app.commands.notes_commands import register_notes_commands
from modules.context.intent_engine import IntentEngine
from modules.context.context_analyzer import ContextAnalyzer

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StudyNotesView(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, fg_color="transparent")
        self.app = app_instance
        self.model = app_instance.notes_model
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.toolbar = ctk.CTkFrame(self, height=50)
        self.toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(self.toolbar, text="📝 My Study Notes", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=10, pady=10)
        
        self.btn_new = ctk.CTkButton(self.toolbar, text="New Note", command=self.new_note)
        self.btn_new.pack(side="left", padx=5)
        
        self.btn_save = ctk.CTkButton(self.toolbar, text="Save Note", command=self.save_note)
        self.btn_save.pack(side="left", padx=5)
        
        self.btn_delete = ctk.CTkButton(self.toolbar, text="Delete", fg_color="#E74C3C", hover_color="#C0392B", command=self.delete_note)
        self.btn_delete.pack(side="left", padx=5)
        
        # Navigation
        ctk.CTkButton(self.toolbar, text="< Prev", width=60, command=self.prev_note).pack(side="right", padx=5)
        self.lbl_tracker = ctk.CTkLabel(self.toolbar, text="0 / 0")
        self.lbl_tracker.pack(side="right", padx=5)
        ctk.CTkButton(self.toolbar, text="Next >", width=60, command=self.next_note).pack(side="right", padx=5)
        
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        self.title_var = ctk.StringVar()
        self.title_entry = ctk.CTkEntry(self.content_frame, textvariable=self.title_var, font=ctk.CTkFont(size=18, weight="bold"), height=40)
        self.title_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.text_area = ctk.CTkTextbox(self.content_frame, font=ctk.CTkFont(size=14))
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
    def refresh_ui(self):
        self.model.reload_notes()
        n = self.model.get_current_note()
        if n:
            self.title_var.set(n['title'])
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", n['content'] or "")
            self.lbl_tracker.configure(text=f"{self.model.current_index + 1} / {len(self.model.notes)}")
        else:
            self.title_var.set("")
            self.text_area.delete("1.0", "end")
            self.lbl_tracker.configure(text="0 / 0")
            
    def next_note(self):
        self.model.next_note()
        self.refresh_ui()
    def prev_note(self):
        self.model.prev_note()
        self.refresh_ui()
    def switch_to_library(self):
        self.app.set_context("LIBRARY")
    def switch_to_notes(self):
        self.app.set_context("STUDY_NOTES")
        
    def new_note(self):
        self.title_var.set("Untitled Note")
        self.text_area.delete("1.0", "end")
        
    def save_note(self):
        title = self.title_var.get()
        content = self.text_area.get("1.0", "end").strip()
        n = self.model.get_current_note()
        
        if n and n['title'] == title:
            # Update
            self.model.repo.update_note(n['id'], {'title': title, 'content': content})
        else:
            # Insert
            self.model.repo.add_note({
                'title': title, 'content': content, 
                'category': 'General', 'created_by_user_id': self.model.current_user_id
            })
        self.refresh_ui()
        
    def delete_note(self):
        n = self.model.get_current_note()
        if n:
            self.model.repo.delete_note(n['id'], self.model.current_user_id)
            self.model.current_index = 0
            self.refresh_ui()


class LibraryApp(ctk.CTk):
    """
    Phase 5 Unified Dual-Dashboard wrapping the 
    AI Command Registry + Intent Engines.
    """
    def __init__(self):
        super().__init__()
        self.title("AI Command Center & Library Manager")
        self.geometry("1500x900")
        self.minsize(1100, 700)
        
        self.auth_manager = AuthManager()
        self.model = LibraryModel()
        self.notes_model = NotesModel(self.model.db)
        
        self.gesture_engine = LibraryGestureEngine()
        self.eye_tracker = EyeTracker()
        self.report_service = ReportService(self.model.repo)
        
        # Phase 5: Command Center Pipeline
        self.intent_engine = IntentEngine("action_mappings.json")
        self.context_analyzer = ContextAnalyzer()
        self.command_registry = CommandRegistry()
        
        self.active_context = "LIBRARY"
        self.command_history = []
        
        # Phase 8: Data-Driven Visual Gesture Map
        self.gesture_images = {}
        from PIL import Image, ImageDraw, ImageFont
        def get_fallback_img(text, color):
            img = Image.new('RGB', (80, 80), color=(44, 62, 80))
            d = ImageDraw.Draw(img)
            try: f = ImageFont.truetype("arialbd.ttf", 36)
            except: f = ImageFont.load_default()
            d.text((40, 40), text, fill=color, font=f, anchor="mm")
            return ctk.CTkImage(light_image=img, size=(60, 60))
            
        try:
            ic_dir = r"C:\Users\tiwar\.gemini\antigravity\brain\8ef62a9a-e9a3-46ea-85fe-be81c5130ba7"
            self.gesture_images = {
                "SWIPE_LEFT": ctk.CTkImage(light_image=Image.open(os.path.join(ic_dir, "swipe_left_1788702166589.png")), size=(60, 60)),
                "SWIPE_RIGHT": ctk.CTkImage(light_image=Image.open(os.path.join(ic_dir, "swipe_right_1788702178366.png")), size=(60, 60)),
                "RIGHT_THUMB_UP": ctk.CTkImage(light_image=Image.open(os.path.join(ic_dir, "thumb_up_1788702191337.png")), size=(60, 60)),
                "RIGHT_THUMB_DOWN": ctk.CTkImage(light_image=Image.open(os.path.join(ic_dir, "thumb_down_1788702205541.png")), size=(60, 60)),
                "NOTES": ctk.CTkImage(light_image=Image.open(os.path.join(ic_dir, "notes_icon_1788702220174.png")), size=(60, 60))
            }
        except Exception as e:
            pass

        fallbacks = {
            "POINT_UP": ("UP", "#F1C40F"),
            "POINT_DOWN": ("DOWN", "#F1C40F"),
            "POINT_LEFT": ("LEFT", "#3498DB"),
            "POINT_RIGHT": ("RIGHT", "#3498DB"),
            "RIGHT_THUMB_UP": ("TH.U", "#2ECC71"),
            "RIGHT_THUMB_DOWN": ("TH.D", "#E74C3C")
        }
        for k, (symbol, c) in fallbacks.items():
            if k not in self.gesture_images:
                self.gesture_images[k] = get_fallback_img(symbol, c)
        
        self.vid_cap = cv2.VideoCapture(0)
        self.is_running = True
        
        self._build_ui()
        
        # Register Commands
        register_library_commands(self.command_registry, self)
        register_notes_commands(self.command_registry, self.notes_view)
        
        if hasattr(self, 'legend_asset_hooks'):
            for k, lbl in self.legend_asset_hooks:
                if k in self.gesture_images:
                    lbl.configure(image=self.gesture_images[k], text="")
                    
        self.set_context("LIBRARY")
        self.after(50, self.update_loop)
        
    def set_context(self, ctx_name: str):
        self.active_context = ctx_name
        self.lbl_context.configure(text=f"CONTEXT: {ctx_name}")
        
        if ctx_name == "LIBRARY":
            self.notes_view.grid_forget()
            self.dashboard.grid(row=0, column=2, sticky="nsew", padx=10)
            self.refresh_ui()
        else:
            self.dashboard.grid_forget()
            self.notes_view.grid(row=0, column=2, sticky="nsew", padx=10)
            self.notes_view.refresh_ui()
            
        self.refresh_available_commands()

    def refresh_available_commands(self):
        # We don't render buttons instantly on dashboard anymore
        pass

    def log_command_history(self, gesture, intent, cmd_name, status, result):
        pass # UI History removed. Audit logs are preserved natively backend if tied to actions.

    def execute_command(self, cmd):
        result = self.command_registry.execute_command(cmd.id, self.model.role)
        return result

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 1. HEADER
        self.header = ctk.CTkFrame(self, fg_color="#1E1E1E", height=60)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.header.pack_propagate(False)
        
        ctk.CTkLabel(self.header, text="TrueEyeball OS", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20)
        
        self.lbl_auth_status = ctk.CTkLabel(self.header, text="Auth: LOCKED", text_color="red", font=ctk.CTkFont(weight="bold"))
        self.lbl_auth_status.pack(side="right", padx=20)
        self.lbl_username = ctk.CTkLabel(self.header, text="User: None")
        self.lbl_username.pack(side="right", padx=10)
        self.lbl_context = ctk.CTkLabel(self.header, text="CONTEXT: LIBRARY", text_color="#F1C40F", font=ctk.CTkFont(weight="bold"))
        self.lbl_context.pack(side="right", padx=30)
        
        # 2. MAIN SPLIT (Sidebar | Command Center | Content)
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.main_content.grid_columnconfigure(2, weight=1) # The active app view
        self.main_content.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar (Camera & System Info) ---
        self.sidebar = ctk.CTkFrame(self.main_content, width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.sidebar.grid_propagate(False)
        self.sidebar.pack_propagate(False)
        
        self.video_canvas = ctk.CTkLabel(self.sidebar, text="", bg_color="black", width=240, height=180)
        self.video_canvas.pack(pady=(10, 5))
        
        # New Legend Frame Below Camera
        self.legend_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.legend_frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(self.legend_frame, text="LIBRARY GESTURE COMMANDS\n" + "-"*35, font=ctk.CTkFont(weight="bold", size=12)).pack(pady=(0, 5))
        
        legend_data = [
            ("POINT_UP", "☝ POINT UP", "Select Book Above"),
            ("POINT_DOWN", "☝ POINT DOWN", "Select Book Below"),
            ("POINT_LEFT", "☝ POINT LEFT", "Select Book Left"),
            ("POINT_RIGHT", "☝ POINT RIGHT", "Select Book Right"),
            ("RIGHT_THUMB_UP", "👍 THUMB UP", "Issue Selected Book"),
            ("RIGHT_THUMB_DOWN", "👎 THUMB DOWN", "Return Selected Book")
        ]
        
        self.legend_asset_hooks = []
        for gkey, gtitle, gdesc in legend_data:
            block = ctk.CTkFrame(self.legend_frame, fg_color="#2C3E50", corner_radius=5)
            block.pack(fill="x", pady=4, padx=2)
            lbl_img = ctk.CTkLabel(block, text="[ICON]")
            lbl_img.pack(pady=(5, 0))
            ctk.CTkLabel(block, text=gdesc, font=ctk.CTkFont(weight="bold", size=13)).pack(pady=(0, 0))
            ctk.CTkLabel(block, text=gtitle, font=ctk.CTkFont(size=11), text_color="#BDC3C7").pack(pady=(0, 5))
            self.legend_asset_hooks.append((gkey, lbl_img))
        
        self.stat_frame_owner = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.stat_frame_owner.pack(side="bottom", fill="x", pady=5)
        # ctk.CTkLabel(self.stat_frame_owner, text="LIBRARY SUMMARY", font=ctk.CTkFont(weight="bold")).pack(pady=(5, 2))
        self.lbl_stat_avail = ctk.CTkLabel(self.stat_frame_owner, text="Available: 0", text_color="#2ECC71")
        self.lbl_stat_avail.pack(anchor="w", padx=20, pady=0)
        self.lbl_stat_trans = ctk.CTkLabel(self.stat_frame_owner, text="Transactions: 0")
        self.lbl_stat_trans.pack(anchor="w", padx=20, pady=2)
        self.btn_export_owner = ctk.CTkButton(self.stat_frame_owner, text="Export Library Report", fg_color="#27AE60", command=self.do_export)
        self.btn_export_owner.pack(pady=(5, 5))
        self.btn_user_mgr = ctk.CTkButton(self.stat_frame_owner, text="User Management", fg_color="#8E44AD", command=self.open_user_management)
        self.btn_user_mgr.pack(pady=(5, 5))
        
        # --- AI COMMAND CENTER PANEL ---
        self.cmd_center = ctk.CTkFrame(self.main_content, width=320, border_color="#F39C12", border_width=2)
        self.cmd_center.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        self.cmd_center.grid_propagate(False)
        
        ctk.CTkLabel(self.cmd_center, text="⚡ AI COMMAND CENTER", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F39C12").pack(pady=10)
        
        # New visual gesture placeholder
        self.lbl_ai_gesture = ctk.CTkLabel(self.cmd_center, text="Detected Gesture:\nNone", justify="left")
        self.lbl_ai_gesture.pack(anchor="w", padx=10, pady=(2, 10))
        
        self.lbl_ai_image = ctk.CTkLabel(self.cmd_center, text="[ Awaiting Gesture ]", width=80, height=80, fg_color="#2A2D2E", corner_radius=8)
        self.lbl_ai_image.pack(pady=5)
        
        self.lbl_ai_intent = ctk.CTkLabel(self.cmd_center, text="Resolved Intent: None", text_color="#3498DB")
        self.lbl_ai_intent.pack(anchor="w", padx=10, pady=(15, 2))
        self.lbl_ai_cmd = ctk.CTkLabel(self.cmd_center, text="Resolved Command: None", text_color="#2ECC71")
        self.lbl_ai_cmd.pack(anchor="w", padx=10, pady=2)
        
        ctk.CTkLabel(self.cmd_center, text="Command Node", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5), anchor="w", padx=10)
        
        self.btn_commands = ctk.CTkButton(self.cmd_center, text="[ AI COMMANDS ]", command=self.open_command_dialog, font=ctk.CTkFont(weight="bold"))
        self.btn_commands.pack(pady=10, fill="x", padx=20)
        
        self.btn_report_status = ctk.CTkButton(self.cmd_center, text="Report Status", command=self.open_report_status, fg_color="#8E44AD")
        self.btn_report_status.pack(pady=10, fill="x", padx=20)
        
        tip_frame = ctk.CTkFrame(self.cmd_center, fg_color="#34495E")
        tip_frame.pack(pady=15, padx=20, fill="x")
        ctk.CTkLabel(tip_frame, text="💡 Tip:\nUse hand gestures to\nnavigate, issue or return\nbooks.", font=ctk.CTkFont(size=12), justify="left").pack(pady=10, padx=10)
        
        # --- LIBRARY APP VIEW ---
        self.dashboard = ctk.CTkFrame(self.main_content)
        self.dashboard.grid_columnconfigure(0, weight=1)
        self.dashboard.grid_rowconfigure(1, weight=1)
        
        self.toolbar = ctk.CTkFrame(self.dashboard, fg_color="transparent", height=50)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.toolbar, textvariable=self.search_var, placeholder_text="Search books by name, ID, or subject...", width=250)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.do_search())
        
        self.sort_var = ctk.StringVar(value="Name (A-Z)")
        self.sort_opts = ctk.CTkOptionMenu(self.toolbar, values=["Name (A-Z)"], variable=self.sort_var, command=lambda v: self.refresh_ui(), width=120)
        self.sort_opts.pack(side="left", padx=5)
        
        self.filter_var = ctk.StringVar(value="All Status")
        self.filter_opts = ctk.CTkOptionMenu(self.toolbar, values=["All Status", "Available", "Issued"], variable=self.filter_var, command=self.do_filter, width=110)
        self.filter_opts.pack(side="left", padx=5)
        
        self.view_var = ctk.StringVar(value="GRID")
        self.view_toggle = ctk.CTkSegmentedButton(self.toolbar, values=["GRID", "LIST"], variable=self.view_var, command=lambda v: self.refresh_ui())
        self.view_toggle.pack(side="right", padx=5)
        
        self.grid_frame = ctk.CTkScrollableFrame(self.dashboard, fg_color="#1a1a1a")
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        self.book_rows = []
        
        self.pagination_frame = ctk.CTkFrame(self.dashboard, fg_color="transparent", height=40)
        self.pagination_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        self.lbl_page_info = ctk.CTkLabel(self.pagination_frame, text="Showing 0 - 0 of 0 books")
        self.lbl_page_info.pack(side="left", padx=10)
        
        self.btn_prev_page = ctk.CTkButton(self.pagination_frame, text="<", width=30, command=self.page_prev)
        self.btn_prev_page.pack(side="left", padx=2)
        self.page_buttons_frame = ctk.CTkFrame(self.pagination_frame, fg_color="transparent")
        self.page_buttons_frame.pack(side="left", padx=5)
        self.btn_next_page = ctk.CTkButton(self.pagination_frame, text=">", width=30, command=self.page_next)
        self.btn_next_page.pack(side="left", padx=2)
        
        self.model.page_size = 24
        self.per_page_var = ctk.StringVar(value="24")
        self.per_page_opts = ctk.CTkOptionMenu(self.pagination_frame, values=["12", "24", "36", "48"], variable=self.per_page_var, command=self.change_page_size, width=70)
        self.per_page_opts.pack(side="right", padx=5)
        ctk.CTkLabel(self.pagination_frame, text="Books per page:").pack(side="right", padx=(5, 2))
        
        # --- STUDY NOTES VIEW ---
        self.notes_view = StudyNotesView(self.main_content, self)

    def do_search(self, *args):
        self.model.search_query = self.search_var.get()
        self.model.page = 1
        self.refresh_ui()

    def do_filter(self, val):
        self.model.status_filter = val if val != "All Status" else "All"
        self.model.page = 1
        self.refresh_ui()

    def page_prev(self):
        if self.model.page > 1:
            self.model.page -= 1
            self.refresh_ui()

    def page_next(self):
        if self.model.page < self.model.total_pages:
            self.model.page += 1
            self.refresh_ui()

    def select_book_up(self):
        if not self.model.books: return
        cols = getattr(self, 'last_grid_cols', 6)
        if self.model.current_index >= cols:
            self.model.current_index -= cols
            self.refresh_ui()

    def select_book_down(self):
        if not self.model.books: return
        total = len(self.model.books)
        cols = getattr(self, 'last_grid_cols', 6)
        next_idx = self.model.current_index + cols
        if next_idx < total:
            self.model.current_index = next_idx
        self.refresh_ui()

    def select_book_left(self):
        if not self.model.books: return
        cols = getattr(self, 'last_grid_cols', 6)
        if self.model.current_index > 0:
            if self.model.current_index % cols != 0:
                self.model.current_index -= 1
                self.refresh_ui()

    def select_book_right(self):
        if not self.model.books: return
        total = len(self.model.books)
        cols = getattr(self, 'last_grid_cols', 6)
        if self.model.current_index < total - 1:
            if (self.model.current_index + 1) % cols != 0:
                self.model.current_index += 1
                self.refresh_ui()

    def goto_page(self, pg):
        self.model.page = pg
        self.refresh_ui()

    def change_page_size(self, val):
        self.model.page_size = int(val)
        self.model.page = 1
        self.refresh_ui()

    def update_pagination_ui(self):
        if not hasattr(self, 'lbl_page_info'): return
        
        start = (self.model.page - 1) * self.model.page_size + 1
        end = min(self.model.page * self.model.page_size, self.model.total_filtered)
        if self.model.total_filtered == 0: start = 0
            
        self.lbl_page_info.configure(text=f"Showing {start} - {end} of {self.model.total_filtered} books")
        
        for w in self.page_buttons_frame.winfo_children(): w.destroy()
        
        p = self.model.page
        tp = self.model.total_pages
        start_p = max(1, p - 2)
        end_p = min(tp, p + 2)
        
        if start_p > 1:
            ctk.CTkButton(self.page_buttons_frame, text="1", width=30, fg_color="gray", command=lambda: self.goto_page(1)).pack(side="left", padx=2)
            if start_p > 2: ctk.CTkLabel(self.page_buttons_frame, text="...").pack(side="left")
            
        for i in range(start_p, end_p + 1):
            color = "#3498DB" if i == p else "gray"
            btn = ctk.CTkButton(self.page_buttons_frame, text=str(i), width=30, fg_color=color, command=lambda pg=i: self.goto_page(pg))
            btn.pack(side="left", padx=2)
            
        if end_p < tp:
            if end_p < tp - 1: ctk.CTkLabel(self.page_buttons_frame, text="...").pack(side="left")
            ctk.CTkButton(self.page_buttons_frame, text=str(tp), width=30, fg_color="gray", command=lambda pg=tp: self.goto_page(pg)).pack(side="left", padx=2)
        
    def do_export(self):
        try:
            path, is_new = self.report_service.generate_report(self.model.role, self.model.current_user_id)
            msg = f"Excel workbook generated successfully at:\n{path}" if is_new else f"Existing Excel workbook updated successfully at:\n{path}"
            messagebox.showinfo("Export Successful", msg)
        except PermissionError as e:
            messagebox.showerror("Access Denied", str(e))
        
    def refresh_ui(self):
        self.model.reload_books()
        
        stats = self.model.get_summary_stats()
        self.lbl_stat_avail.configure(text=f"Available: {stats['available']}")
        self.lbl_stat_trans.configure(text=f"Transactions: {stats['transactions']}")
        
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.book_rows.clear()
        
        if not self.model.books: 
            self.update_pagination_ui()
            return
            
        view_mode = getattr(self, 'view_var', ctk.StringVar(value="GRID")).get()
        cols = 6
        gw = self.grid_frame.winfo_width()
        if gw > 100:
            cols = max(1, gw // 190)
        self.last_grid_cols = cols
            
        for i, book in enumerate(self.model.books):
            is_selected = (i == self.model.current_index)
            
            if view_mode == "LIST":
                row_color = "#34495E" if is_selected else "#2A2D2E"
                row = ctk.CTkFrame(self.grid_frame, fg_color=row_color, corner_radius=5)
                row.pack(fill="x", pady=2, padx=2)
                
                ctk.CTkLabel(row, text=book.book_code, width=80, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=book.title, width=350, anchor="w").pack(side="left", padx=5)
                
                scolor = "#2ECC71" if book.status == "Available" else "#E74C3C"
                ctk.CTkLabel(row, text=book.status, width=100, anchor="w", text_color=scolor).pack(side="left", padx=5)
                self.book_rows.append(row)
            else:
                row_color = "black" if is_selected else "#2C3E50"
                bw = 3 if is_selected else 0
                bc = "#F1C40F" if is_selected else None
                
                card = ctk.CTkFrame(self.grid_frame, fg_color=row_color, corner_radius=8, width=170, height=240, border_width=bw, border_color=bc)
                card.grid_propagate(False)
                card.pack_propagate(False)
                
                r, c = divmod(i, cols)
                card.grid(row=r, column=c, padx=10, pady=10, sticky="n")
                
                if is_selected:
                    folder_tab = ctk.CTkFrame(card, fg_color="#F1C40F", height=12, corner_radius=4)
                    folder_tab.pack(fill="x", side="top", padx=0, pady=0)
                    ctk.CTkLabel(card, text="★ SELECTED", font=ctk.CTkFont(weight="bold", size=10), text_color="#F1C40F").pack(pady=(2, 0))
                else:
                    folder_tab = ctk.CTkFrame(card, fg_color="#F1C40F", height=12, corner_radius=4)
                    folder_tab.pack(fill="x", side="top", padx=0, pady=0)
                
                h_val = sum(ord(char) for char in book.title)
                colors = ["#2E4053", "#1ABC9C", "#9B59B6", "#E67E22", "#34495E", "#16A085", "#8E44AD"]
                c_bg = colors[h_val % len(colors)]
                
                cover_lbl = ctk.CTkLabel(card, text=book.title[:2]+"...", bg_color=c_bg, width=120, height=140 if not is_selected else 115, font=ctk.CTkFont(size=24, weight="bold"))
                cover_lbl.pack(pady=(12, 5))
                
                title_font = ctk.CTkFont(weight="bold", size=14) if is_selected else ctk.CTkFont(weight="bold", size=12)
                t_str = book.title
                if len(t_str) > 20: t_str = t_str[:17] + "..."
                title_lbl = ctk.CTkLabel(card, text=t_str, font=title_font)
                title_lbl.pack(pady=(0, 2))
                
                scolor = "#2ECC71" if book.status == "Available" else "#E74C3C"
                status_lbl = ctk.CTkLabel(card, text="● " + book.status, text_color=scolor, font=ctk.CTkFont(size=12))
                status_lbl.pack()
                
                self.book_rows.append(card)
                
        if self.model.books and self.book_rows:
            target_idx = self.model.current_index
            if target_idx < len(self.book_rows):
                if view_mode == "GRID":
                    items_per_col = (len(self.book_rows) + cols - 1) // cols
                    frac = (target_idx // cols) / max(1, items_per_col)
                else:
                    frac = target_idx / len(self.book_rows)
                
                frac = max(0.0, frac - 0.1)
                try:
                    self.grid_frame._parent_canvas.yview_moveto(frac)
                except Exception:
                    pass
                    
        self.update_pagination_ui()

    def enforce_dashboard_role(self):
        if self.model.role in ["OWNER", "STAFF"]:
            self.lbl_auth_status.configure(text=f"Auth: {self.model.role}", text_color="green")
            self.lbl_username.configure(text=f"User: {getattr(self.model, 'display_name', self.model.current_user_id)}")
            self.notes_model.current_user_id = self.model.current_user_id
        else:
            self.lbl_auth_status.configure(text="Auth: LOCKED", text_color="red")
            self.lbl_username.configure(text="User: None")
            self.notes_model.current_user_id = None
            
        self.refresh_available_commands()
        
    def handle_gesture(self, gesture):
        if not gesture: return
        self.lbl_ai_gesture.configure(text=f"Detected Gesture:\n{gesture}")
        
        # Map dynamic image if available
        gimg = self.gesture_images.get(gesture)
        if gimg:
            self.lbl_ai_image.configure(image=gimg, text="")
        else:
            self.lbl_ai_image.configure(image=None, text="[ No Image ]")
        
        # Pipeline 1: Intent Resolution
        intent = self.intent_engine.evaluate(self.active_context, gesture)
        self.lbl_ai_intent.configure(text=f"Resolved Intent: {intent}")
        if intent == "NONE": return
        
        # Pipeline 2: Command Search
        cmd = self.command_registry.resolve_intent(self.active_context, intent)
        if not cmd:
            self.lbl_ai_cmd.configure(text="Command: None (Not Registered for Context)", text_color="orange")
            self.log_command_history(gesture, intent, "UNKNOWN", "DENIED", None)
            return
            
        self.lbl_ai_cmd.configure(text=f"Command: {cmd.display_name}", text_color="#2ECC71")
        
        # Avoid firing during modals
        if self.focus_get() is not None:
            active = self.focus_get().winfo_toplevel()
            if active != self:
                return
                
        # Pipeline 3: Execute Command
        result = self.execute_command(cmd)
        
        if result['status'] == 'denied':
            messagebox.showerror("RBAC Denied", result['error'])
            
        import time
        now = time.time()
        if not hasattr(self, '_last_log_time'):
            self._last_log_time = 0
            
        if now - self._last_log_time > 1.0:
            self.log_command_history(gesture, intent, cmd.id, result['status'], result.get('result'))
            self._last_log_time = now
        
        # If UI refreshed inside handler, we shouldn't worry
        if self.active_context == "LIBRARY":
            self.refresh_ui()

    def open_command_dialog(self):
        if not self.model.current_user_id:
            messagebox.showerror("Error", "Authentication required")
            return
            
        dlg = ctk.CTkToplevel(self)
        dlg.geometry("400x700")
        dlg.title("AI COMMANDS")
        dlg.attributes("-topmost", True)
        
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(sf, text="AI COMMANDS", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(sf, text=f"Context: {self.active_context}").pack()
        ctk.CTkLabel(sf, text=f"User: {self.model.display_name}").pack()
        ctk.CTkLabel(sf, text=f"Role: {self.model.role}").pack(pady=(0, 10))
        
        ctk.CTkLabel(sf, text="-"*40).pack(pady=5)
        
        cmds = self.command_registry.get_available_commands(self.active_context, self.model.role)
        for cmd in cmds:
            color = "#E74C3C" if not cmd.is_safe else "#3498DB"
            
            f_cmd = ctk.CTkFrame(sf, fg_color="#2C3E50", corner_radius=8)
            f_cmd.pack(pady=8, fill="x", padx=10)
            
            g_img = None
            for g, i in self.intent_engine.bindings.get(self.active_context, {}).items():
                if i == cmd.id:
                    g_img = self.gesture_images.get(g)
                    break
                    
            info_f = ctk.CTkFrame(f_cmd, fg_color="transparent")
            info_f.pack(side="left", padx=15, pady=10)
            
            if g_img:
                ctk.CTkLabel(info_f, image=g_img, text="").pack(pady=(0, 5))
            else:
                ctk.CTkLabel(info_f, text="[Image]", width=60).pack(pady=(0, 5))
                
            ctk.CTkLabel(info_f, text=cmd.display_name, font=ctk.CTkFont(weight="bold", size=13)).pack()
            
            btn = ctk.CTkButton(
                f_cmd, 
                text="Execute", 
                fg_color=color, 
                command=lambda c=cmd, d=dlg: [self.execute_command(c), d.destroy()],
                width=100
            )
            btn.pack(side="right", padx=15)
            
        ctk.CTkLabel(sf, text="-"*40).pack(pady=5)
        ctk.CTkButton(sf, text="[ Close ]", fg_color="gray", command=dlg.destroy).pack(pady=10, fill="x", padx=40)
        
    def open_report_status(self):
        if not self.model.current_user_id:
            messagebox.showerror("Error", "Authentication required")
            return
            
        dlg = ctk.CTkToplevel(self)
        dlg.geometry("500x700")
        dlg.title("LIBRARY REPORT STATUS")
        dlg.attributes("-topmost", True)
        
        f = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(f, text="LIBRARY REPORT STATUS", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
        ctk.CTkLabel(f, text=f"Generated For: {self.model.display_name}").pack()
        ctk.CTkLabel(f, text=f"Role: {self.model.role}").pack()
        ts = time.strftime("%H:%M:%S")
        ctk.CTkLabel(f, text=f"Generated At: {ts}").pack(pady=(0, 10))
        
        ctk.CTkLabel(f, text="-"*60).pack()
        
        if self.model.role == "OWNER":
            books = self.model.repo.list_books()
            txns = self.model.repo.get_all_transactions()
        else:
            txns = self.model.repo.get_lifecycle_transactions(self.model.current_user_id)
            book_ids = set(t['book_id'] for t in txns)
            books = [self.model.repo.get_book(bid) for bid in book_ids]
            
        avail = sum(1 for b in books if b['status'] == "Available")
        iss = sum(1 for b in books if b['status'] == "Issued")
        
        ctk.CTkLabel(f, text=f"TOTAL BOOKS: {len(books)}", font=ctk.CTkFont(weight="bold")).pack(pady=2, anchor='w')
        ctk.CTkLabel(f, text=f"AVAILABLE: {avail}", text_color="green", font=ctk.CTkFont(weight="bold")).pack(pady=2, anchor='w')
        ctk.CTkLabel(f, text=f"ISSUED: {iss}", text_color="red", font=ctk.CTkFont(weight="bold")).pack(pady=(2, 10), anchor='w')
        
        ctk.CTkLabel(f, text="-"*60).pack()
        ctk.CTkLabel(f, text="ISSUED BOOKS/LIFECYCLES", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5), anchor='w')
        
        # Group txns by book_history equivalent logic
        book_history = {}
        for t in reversed(txns):
            bid = t['book_id']
            if bid not in book_history: book_history[bid] = {'issue': None, 'return': None}
            if t['action'] == 'ISSUE':
                book_history[bid]['issue'] = t
                book_history[bid]['return'] = None
            elif t['action'] == 'RETURN':
                book_history[bid]['return'] = t
                
        for b in books:
            bid = b['id']
            hist = book_history.get(bid, {})
            iss_t = hist.get('issue')
            ret_t = hist.get('return')
            
            borrower = iss_t.get('user_id') if iss_t else b.get('issued_to_user_id')
            issued_by = iss_t.get('staff_user_id') if iss_t else b.get('issued_by_user_id')
            returned_by = ret_t.get('staff_user_id') if ret_t else None
            
            # Print state if it was issued OR returned
            if iss_t or ret_t or b.get('status') == 'Issued':
                ctk.CTkLabel(f, text=f"[{b.get('book_code')}] {b.get('title')}", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(5, 0))
                if returned_by:
                    ctk.CTkLabel(f, text=f"  Returned By: {returned_by}", text_color="cyan").pack(anchor='w')
                    ctk.CTkLabel(f, text=f"  Originally Issued By: {issued_by} (To: {borrower})", text_color="gray").pack(anchor='w')
                elif issued_by:
                    ctk.CTkLabel(f, text=f"  Issued To: {borrower}", text_color="#E67E22").pack(anchor='w')
                    ctk.CTkLabel(f, text=f"  Issued By: {issued_by}", text_color="gray").pack(anchor='w')

    def open_user_management(self):
        try:
            PermissionManager.require_permission(self.model.role, Permission.MANAGE_STAFF)
        except PermissionError as e:
            messagebox.showerror("Access Denied", str(e))
            return
            
        dlg = ctk.CTkToplevel(self)
        dlg.geometry("500x500")
        dlg.title("USER MANAGEMENT")
        dlg.attributes("-topmost", True)
        
        f = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(f, text="USER MANAGEMENT", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
        
        counts = self.model.repo.get_role_counts()
        ctk.CTkLabel(f, text=f"Active Staff: {counts.get('STAFF', 0)}/10").pack()
        ctk.CTkLabel(f, text="-"*60).pack(pady=10)
        
        def refresh_list():
            for w in [c for c in f.winfo_children() if c not in f.winfo_children()[:3]]:
                w.destroy()
            
            users = self.model.repo.list_users()
            for u in users:
                row = ctk.CTkFrame(f, fg_color="#2C3E50")
                row.pack(fill="x", pady=4)
                
                is_active = u.get('active', 1) == 1
                color = "#2ECC71" if is_active else "#E74C3C"
                status_txt = "ACTIVE" if is_active else "DEACTIVATED"
                
                ctk.CTkLabel(row, text=f"{u['username']} ({u['role']})", width=200, anchor="w").pack(side="left", padx=10)
                ctk.CTkLabel(row, text=status_txt, text_color=color, width=100).pack(side="left", padx=5)
                
                if is_active and u['username'] != self.model.current_user_id:
                    btn = ctk.CTkButton(row, text="Deactivate", width=80, fg_color="#E74C3C", hover_color="#C0392B",
                                        command=lambda un=u['username']: confirm_deactivate(un))
                    btn.pack(side="right", padx=10, pady=5)
        
        def confirm_deactivate(target_username):
            if messagebox.askyesno("Confirm Deactivation", f"Are you sure you want to deactivate {target_username}?"):
                self.model.repo.deactivate_user(target_username)
                messagebox.showinfo("Success", f"{target_username} has been deactivated.")
                refresh_list()
                self.refresh_available_commands()
                
        refresh_list()

    def update_loop(self):
        if not self.is_running: return
        
        ret, frame = self.vid_cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            
            frame, eye_status, auth_landmarks = self.eye_tracker.process(frame)
            auth_state, current_uid, auth_conf = self.auth_manager.process_face(auth_landmarks)
            auth_status = (auth_state == "AUTHENTICATED")
            
            # Detect Role Changes
            if auth_status and self.model.current_user_id != current_uid:
                db_user = self.model.repo.get_user_by_username(current_uid)
                if db_user and db_user.get('active', 1) == 1:
                    self.model.set_user(current_uid)
                    self.model.role = db_user.get('role', 'STAFF')
                    name = db_user.get('display_name', current_uid)
                    self.model.display_name = name
                    self.enforce_dashboard_role()
                else:
                    self.model.set_user(None)
                    self.lbl_auth_status.configure(text="Auth: DEACTIVATED", text_color="red")
                    self.lbl_username.configure(text="User: None")
                    self.notes_model.current_user_id = None
                    self.refresh_available_commands()
                    auth_status = False
                    
            elif not auth_status and self.model.current_user_id is not None:
                self.model.set_user(None)
                self.enforce_dashboard_role()
                
            if auth_status:
                frame_mod, gesture = self.gesture_engine.process(frame)
                if gesture:
                    self.handle_gesture(gesture)
            else:
                frame_mod = frame
                
            rgb_frame = cv2.cvtColor(frame_mod, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            ctk_image = ctk.CTkImage(light_image=pil_image, size=(240, 180))
            self.video_canvas.configure(image=ctk_image)
            self.video_canvas._image = ctk_image
        
        self.after(30, self.update_loop)

    def on_closing(self):
        self.is_running = False
        if self.vid_cap.isOpened():
            self.vid_cap.release()
        self.destroy()

if __name__ == "__main__":
    app = LibraryApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
