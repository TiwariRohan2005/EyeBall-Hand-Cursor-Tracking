class AdaptiveConfig:
    """
    Central fallback configuration serving as a safe fail-state if adaptive 
    learning modules are absent or corrupted. Stores all mathematical baseline constants.
    """
    def __init__(self):
        # Eye Tracking & Blinking Fallsbacks
        self.blink_threshold_ratio = 0.65
        self.min_blink_time = 0.15
        self.max_blink_time = 0.8
        
        # Gestures & Cursor Fallsbacks
        self.cursor_base_alpha = 0.2
        self.cursor_deadzone = 2.0
        self.gesture_cooldown = 0.5
        
        # Intelligent Interaction Kinematics Fallsbacks
        self.stability_radius = 25.0
        self.hover_time_required = 0.8
        
    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data):
        c = cls()
        if not data: return c
        c.blink_threshold_ratio = data.get("blink_threshold_ratio", c.blink_threshold_ratio)
        c.min_blink_time = data.get("min_blink_time", c.min_blink_time)
        c.max_blink_time = data.get("max_blink_time", c.max_blink_time)
        c.cursor_base_alpha = data.get("cursor_base_alpha", c.cursor_base_alpha)
        c.cursor_deadzone = data.get("cursor_deadzone", c.cursor_deadzone)
        c.gesture_cooldown = data.get("gesture_cooldown", c.gesture_cooldown)
        c.stability_radius = data.get("stability_radius", c.stability_radius)
        c.hover_time_required = data.get("hover_time_required", c.hover_time_required)
        return c
