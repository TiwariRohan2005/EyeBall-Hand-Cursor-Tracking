import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .models import LibraryModel

class SessionReportUI(ctk.CTkToplevel):
    def __init__(self, master, model: LibraryModel):
        super().__init__(master)
        self.title("Library Session Report")
        self.geometry("800x600")
        self.attributes('-topmost', True) # Keep overlay on top
        self.model = model
        
        self._build_ui()
        
    def _build_ui(self):
        title = ctk.CTkLabel(self, text="Session Statistics", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=10)
        
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        duration = f"{self.model.stats.get_duration():.1f}s"
        total = self.model.stats.total_books
        
        ctk.CTkLabel(stats_frame, text=f"Duration: {duration}").grid(row=0, column=0, padx=20)
        ctk.CTkLabel(stats_frame, text=f"Total Swipes: {self.model.stats.swipe_count}").grid(row=0, column=1, padx=20)
        ctk.CTkLabel(stats_frame, text=f"Total Books: {total}").grid(row=0, column=2, padx=20)
        
        self.fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
        self.fig.patch.set_facecolor('#2b2b2b')
        ax1.set_facecolor('#2b2b2b')
        ax2.set_facecolor('#2b2b2b')
        
        # Pie Chart: Issued vs Available
        current_issued = sum(1 for b in self.model.books if b.status == "Issued")
        available = total - current_issued
        
        labels = 'Available', 'Issued'
        sizes = [available, current_issued]
        colors = ['#2ECC71', '#E74C3C']
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'color':"w"})
        ax1.set_title('Current Book Status', color='w')
        
        # Bar Chart: Actions
        actions = ['Issues', 'Returns']
        counts = [self.model.stats.issued_count, self.model.stats.returned_count]
        
        ax2.bar(actions, counts, color=['#3498DB', '#9B59B6'])
        ax2.set_title('Session Actions', color='w')
        ax2.tick_params(colors='w')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        
        close_btn = ctk.CTkButton(self, text="Close Report", command=self.destroy)
        close_btn.pack(pady=10)

