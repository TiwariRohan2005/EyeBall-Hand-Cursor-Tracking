import customtkinter as ctk
import time
from tkinter import messagebox

class BookDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, book, model):
        super().__init__(parent)
        self.title("Book Details")
        self.geometry("600x600")
        self.book = book
        self.model = model
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Meta info
        meta_frame = ctk.CTkFrame(self)
        meta_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(meta_frame, text=f"Title: {book.title}", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=5, padx=10)
        ctk.CTkLabel(meta_frame, text=f"Code: {book.book_code} | Author: {book.author}", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10)
        status_color = "#2ECC71" if book.status == "Available" else "#E74C3C"
        ctk.CTkLabel(meta_frame, text=f"Status: {book.status}", font=ctk.CTkFont(size=14, weight="bold"), text_color=status_color).pack(anchor="w", padx=10)
        
        if book.status == "Issued" and book.issued_to_user_id:
            ctk.CTkLabel(meta_frame, text=f"Issued To: {book.issued_to_user_id}").pack(anchor="w", padx=10)
            
        # Transactions logic
        ctk.CTkLabel(self, text="Transaction History", font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=0, sticky="w", padx=20)
        
        self.history_frame = ctk.CTkScrollableFrame(self)
        self.history_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.load_history()
        
    def load_history(self):
        history = self.model.repo.get_book_history(self.book.id)
        if not history:
            ctk.CTkLabel(self.history_frame, text="No transaction history available.", text_color="gray").pack(pady=20)
            return
            
        for t in history:
            f = ctk.CTkFrame(self.history_frame, fg_color="#2A2D2E", corner_radius=5)
            f.pack(fill="x", pady=5, padx=5)
            action_color = "#3498DB" if t['action'] == "ISSUE" else "#E67E22"
            
            # Format time
            dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t['timestamp'])) if t['timestamp'] else "Unknown"
            
            ctk.CTkLabel(f, text=f"{t['action']}", font=ctk.CTkFont(weight="bold"), text_color=action_color).pack(side="left", padx=10, pady=5)
            user = t['user_id'] or "Unknown"
            ctk.CTkLabel(f, text=f"User: {user}").pack(side="left", padx=10)
            ctk.CTkLabel(f, text=f"{dt}", text_color="gray").pack(side="right", padx=10)

class BookFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, model, book_id=None, on_success=None):
        super().__init__(parent)
        self.title("Add Book" if not book_id else "Edit Book")
        self.geometry("500x600")
        self.model = model
        self.book_id = book_id
        self.on_success = on_success
        
        self.grid_columnconfigure(1, weight=1)
        
        # Form fields
        self.entries = {}
        
        fields = [
            ("Book Code *", "book_code"),
            ("Title *", "title"),
            ("Author *", "author"),
            ("ISBN", "isbn"),
            ("Category", "category"),
        ]
        
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(self, text=label).grid(row=i, column=0, padx=10, pady=10, sticky="e")
            entry = ctk.CTkEntry(self, width=250)
            entry.grid(row=i, column=1, padx=10, pady=10, sticky="w")
            self.entries[key] = entry
            
        # load logic
        if self.book_id:
            b = self.model.repo.get_book(self.book_id)
            if b:
                for k, v in self.entries.items():
                    if b.get(k):
                        v.insert(0, str(b[k]))
                # Cannot edit Book Code on edit to prevent accidental constraints breakage unless needed
                self.entries['book_code'].configure(state="disabled")
                        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(btn_frame, text="Save", command=self.save).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", command=self.destroy).pack(side="left", padx=10)

    def save(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}
        
        # Validation
        if not data.get('book_code') and not self.book_id:
            messagebox.showerror("Error", "Book Code is required.")
            return
        if not data.get('title'):
            messagebox.showerror("Error", "Title is required.")
            return
        if not data.get('author'):
            messagebox.showerror("Error", "Author is required.")
            return
            
        try:
            if self.book_id:
                # Update
                # Exclude book code from update payload just in case
                if 'book_code' in data: del data['book_code']
                self.model.repo.update_book(self.book_id, data)
            else:
                self.model.repo.add_book(data)
                
            if self.on_success:
                self.on_success()
            self.destroy()
            messagebox.showinfo("Success", "Book saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
