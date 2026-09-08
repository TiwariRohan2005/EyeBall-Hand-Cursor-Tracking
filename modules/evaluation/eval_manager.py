import threading
import queue
import time
from .benchmark_report import BenchmarkReportGenerator

class EvaluationManager:
    """
    Central Asynchronous Singleton for recording AI framework telemetry limits.
    All modules push metrics to this isolated thread.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EvaluationManager, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self.metrics_queue = queue.Queue(maxsize=10000)
        self.running = True
        
        # In-Memory Session Storage
        self.session_data = {
            "cursor": [],
            "hand": [],
            "blink": [],
            "gesture": [],
            "auth": [],
            "prediction": [],
            "keyboard": []
        }
        
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def log_metric(self, category: str, payload: dict):
        """
        Thread-safe, non-blocking telemetry injection API. 
        Category must belong to standard domains (e.g., 'cursor', 'auth').
        """
        if not self.running: return
        
        event = {
            "timestamp": time.time(),
            "category": category,
            "data": payload
        }
        try:
            self.metrics_queue.put_nowait(event)
        except queue.Full:
            pass # Drop telemtry if we strangely backup to prevent UI freezing

    def _process_queue(self):
        while self.running or not self.metrics_queue.empty():
            try:
                event = self.metrics_queue.get(timeout=0.1)
                cat = event["category"]
                
                if cat in self.session_data:
                    self.session_data[cat].append(event)
                    
                self.metrics_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Evaluation Warning] Processing Error: {e}")

    def shutdown_and_export(self):
        """
        Gracefully terminate the async observer and flush mathematical metric averages 
        to local JSON/CSV/Graph dashboards.
        """
        self.running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
            
        generator = BenchmarkReportGenerator(self.session_data)
        generator.export_all()
