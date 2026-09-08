import json
import os
from .config_manager import AdaptiveConfig

class AdaptiveLearningEngine:
    """
    Operates during main.py (Runtime). Reads the personalized profile, injects 
    custom mathematical tolerances into the submodules, and implements EMA 
    decay/growth as variables drift throughout the session.
    """
    def __init__(self, username):
        self.username = username
        self.profile_path = f".user_{username}_learning.json"
        
        self.data_store = self._load()
        self.config = AdaptiveConfig.from_dict(self.data_store.get("adaptive_config", {}))

    def _load(self):
        if not os.path.exists(self.profile_path):
            return {}
        try:
            with open(self.profile_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        self.data_store["adaptive_config"] = self.config.to_dict()
        with open(self.profile_path, "w") as f:
            json.dump(self.data_store, f)

    def get_baseline_ears(self):
        """Yields dynamically discovered EAR bases, or safe defaults if none exist (legacy user)."""
        left = self.data_store.get("baseline_left_ear", 0.28)
        right = self.data_store.get("baseline_right_ear", 0.28)
        return left, right
        
    def adapt_stability(self, misfire=True):
        """
        Called when a Hover triggers but is violently cancelled instantly (Misfire).
        Uses EMA to incrementally decrease the stability threshold, meaning the system learns
        the user has naturally jittery hands today.
        """
        alpha = 0.05 # 5% Learning Rate Smoothing Factor
        if misfire:
            # Expand tolerance (making it easier) up to 45px
            target = min(self.config.stability_radius + 5.0, 45.0)
            self.config.stability_radius = (self.config.stability_radius * (1 - alpha)) + (target * alpha)
        else:
            # Successful smooth operation slowly regains strict tolerance
            target = max(self.config.stability_radius - 1.0, 15.0)
            self.config.stability_radius = (self.config.stability_radius * (1 - alpha)) + (target * alpha)
            
    def adapt_blink_timing(self, felt_fatigued=True):
        """
        Stretches the max blink time slightly if the user is keeping their eyes closed longer
        than the hardcoded limit, preventing failed trigger recognition.
        """
        alpha = 0.02
        if felt_fatigued:
            # Widen blink time limit slightly
            target = min(self.config.max_blink_time + 0.3, 1.5)
            self.config.max_blink_time = (self.config.max_blink_time * (1 - alpha)) + (target * alpha)
            
    def get_config(self) -> AdaptiveConfig:
        return self.config
