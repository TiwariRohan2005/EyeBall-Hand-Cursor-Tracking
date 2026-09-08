import time
import math
from collections import deque
import numpy as np

class InteractionEngine:
    def __init__(self, adaptive_engine=None):
        self.adaptive_engine = adaptive_engine
        
        # Configuration Thresholds (Fallback Defaults)
        self.history_size = 15                 # Number of frames to track for stability
        self.stability_radius = 25.0           # Max pixel variance allowed for "stable"
        self.hover_time_required = 0.8         # Seconds to reach 100% hover confidence
        self.velocity_projection_frames = 10   # Multiplier for intent prediction raycasting
        
        # State Tracking
        self.history = deque(maxlen=self.history_size)
        self.last_time = time.time()
        
        self.current_target_key_id = None
        self.current_hover_time = 0.0
        
    def _dist(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def process(self, cursor_x, cursor_y, keyboard_manager):
        """
        Process the raw cursor position through the intelligence engine.
        Modifies keyboard key states dynamically based on intent and stability.
        Returns: active_key, hover_confidence (0.0 to 1.0), is_ready  
        """
        now = time.time()
        dt = max(now - self.last_time, 0.001)
        self.last_time = now

        # Add to history
        self.history.append((cursor_x, cursor_y))

        # 1. Compute Intent (Velocity & Direction)
        intent_x, intent_y = cursor_x, cursor_y
        if len(self.history) >= 2:
            dx = cursor_x - self.history[0][0]
            dy = cursor_y - self.history[0][1]
            # Average velocity over history window
            vx = dx / len(self.history)
            vy = dy / len(self.history)
            
            # Project forward
            intent_x = cursor_x + (vx * self.velocity_projection_frames)
            intent_y = cursor_y + (vy * self.velocity_projection_frames)

        from modules.calibration.config_manager import AdaptiveConfig
        if self.adaptive_engine:
            config = self.adaptive_engine.get_config()
        else:
            config = AdaptiveConfig()

        # 2. Compute Stability (Variance)
        is_stable = False
        if len(self.history) == self.history_size:
            # Calculate centroid of history
            cx = sum(p[0] for p in self.history) / self.history_size
            cy = sum(p[1] for p in self.history) / self.history_size
            
            # Check maximum deviation from centroid
            max_dev = max(self._dist(p, (cx, cy)) for p in self.history)
            if max_dev < config.stability_radius:
                is_stable = True

        # 3. Resolve Current Key
        physically_hitting_key = None
        for k in keyboard_manager.keys:
            if k.check_hit(cursor_x, cursor_y):
                physically_hitting_key = k
                break

        # 4. Handle Hover Progress & Confidence
        if physically_hitting_key and is_stable:
            if self.current_target_key_id == physically_hitting_key.id:
                # Continuing stable hover
                self.current_hover_time += dt
            else:
                # Started hovering a new key
                self.current_target_key_id = physically_hitting_key.id
                self.current_hover_time = dt
        else:
            # Cursor moved too fast, jittered, or moved off key
            self.current_target_key_id = None
            self.current_hover_time = 0.0

        # Calculate Confidence 0.0 to 1.0
        hover_confidence = min(self.current_hover_time / config.hover_time_required, 1.0)
        is_ready = (hover_confidence == 1.0)

        # 5. Apply Visual States to Keyboard
        for k in keyboard_manager.keys:
            if k.state in ["disabled", "selected"]:
                k.hover_confidence = 0.0 # reset progress visually
                continue
                
            # Define State Priority: Ready > Progressing > Intent > Idle
            if k.id == self.current_target_key_id:
                k.hover_confidence = hover_confidence
                if is_ready:
                    k.update_state("ready")
                elif hover_confidence > 0:
                    k.update_state("progressing")
            else:
                k.hover_confidence = 0.0
                # Check Intent Prediction Highlight (if not dwelling)
                if hover_confidence == 0.0 and k.check_hit(intent_x, intent_y):
                    k.update_state("intent_target")
                else:
                    # Reset to idle if it was just hovering/intent
                    if k.state in ["ready", "progressing", "intent_target", "hover"]:
                        k.update_state("idle")

        active_key = physically_hitting_key if self.current_target_key_id else None
        return active_key, hover_confidence, is_ready
