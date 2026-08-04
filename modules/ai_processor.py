import time
import math

class CursorStabilizer:
    def __init__(self):
        # EMA parameters
        self.base_alpha = 0.2  # Smoothing factor
        self.prev_x = 0
        self.prev_y = 0
        
        # Velocity tracking
        self.last_time = time.time()
        
        # Jitter filtering deadzone (in pixels)
        self.deadzone = 2.0
        
        # High-confidence threshold
        self.min_confidence = 0.5
        
        self.initialized = False

    def process(self, hand_data):
        if not hand_data:
            return None
            
        hand_pos, confidence = hand_data
        
        # 1. Confidence Filtering
        if confidence < self.min_confidence:
            return None
            
        raw_x, raw_y = hand_pos
        
        if not self.initialized:
            self.prev_x = raw_x
            self.prev_y = raw_y
            self.initialized = True
            self.last_time = time.time()
            return raw_x, raw_y
            
        # 2. Jitter Prevention (Deadzone)
        dist = math.hypot(raw_x - self.prev_x, raw_y - self.prev_y)
        if dist < self.deadzone:
            # Drop microscopic noisy movements, use previous
            return self.prev_x, self.prev_y
            
        now = time.time()
        dt = max(now - self.last_time, 0.001)
        self.last_time = now
        
        # 3. Velocity-based dynamic smoothing
        # Velocity in pixels/sec
        velocity = dist / dt
        
        # Increase alpha proportionally to velocity
        # If moving fast (e.g. > 2000 pixels/sec), alpha approaches 1 (no smoothing, highly responsive)
        # If moving slow, alpha stays near base_alpha (highly smoothed)
        dynamic_alpha = self.base_alpha + (velocity / 2000.0)
        alpha = max(0.05, min(1.0, dynamic_alpha))
        
        # 4. EMA Smoothing Formula
        smoothed_x = self.prev_x + alpha * (raw_x - self.prev_x)
        smoothed_y = self.prev_y + alpha * (raw_y - self.prev_y)
        
        self.prev_x = smoothed_x
        self.prev_y = smoothed_y
        
        return smoothed_x, smoothed_y
