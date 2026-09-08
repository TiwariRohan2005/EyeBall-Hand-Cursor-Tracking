import os
import json
import csv

class BenchmarkReportGenerator:
    """
    Synchronously crunches the millions of mathematical datapoints captured 
    by the EvaluationManager Queue into structured reports when the app closes.
    """
    def __init__(self, session_data: dict):
        self.session_data = session_data
        
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def export_all(self):
        print("\n[~] Generating AI Benchmarking Reports...")
        self._export_json()
        self._export_csvs()
        self._generate_graphs()
        print(f"[+] Benchmarking exports deeply cached in '{self.log_dir}' folder.")

    def _export_json(self):
        filepath = os.path.join(self.log_dir, "evaluation_session.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(self.session_data, f, indent=4)
        except Exception as e:
            print(f"Error saving JSON: {e}")

    def _export_csvs(self):
        # We spawn a single CSV per metric category
        for category, events in self.session_data.items():
            if not events: continue
            
            filepath = os.path.join(self.log_dir, f"{category}_metrics.csv")
            try:
                with open(filepath, 'w', newline='') as f:
                    # Discover all potential keys across variable dynamic payloads to write header
                    all_keys = set()
                    for ev in events:
                        all_keys.update(ev['data'].keys())
                        
                    header = ['timestamp'] + list(sorted(all_keys))
                    writer = csv.DictWriter(f, fieldnames=header)
                    writer.writeheader()
                    
                    for ev in events:
                        row = {'timestamp': ev['timestamp']}
                        row.update(ev['data'])
                        writer.writerow(row)
            except Exception as e:
                print(f"Error saving CSV for {category}: {e}")

    def _generate_graphs(self):
        """
        Gracefully leverages matplotlib if available locally to build historic diagrams.
        """
        try:
            import matplotlib.pyplot as plt
            
            # Example: Graph Auth Confidence over exactly this session
            auth_events = self.session_data.get("auth", [])
            if auth_events:
                times = [ev["timestamp"] - auth_events[0]["timestamp"] for ev in auth_events if "confidence" in ev["data"]]
                scores = [ev["data"]["confidence"] for ev in auth_events if "confidence" in ev["data"]]
                
                if times and scores:
                    plt.figure(figsize=(10, 5))
                    plt.plot(times, scores, marker='o', linestyle='-', color='b')
                    plt.title("Authentication Confidence Over Time")
                    plt.xlabel("Session Time (seconds)")
                    plt.ylabel("Cosine Similarity Conf")
                    plt.ylim([0, 1.1])
                    plt.grid(True)
                    plt.savefig(os.path.join(self.log_dir, "auth_confidence_plot.png"))
                    plt.close()
                    
        except ImportError:
            pass # Matplotlib unsupported on this local machine environment
