import cv2

class Key:
    def __init__(self, key_id, label, width_multiplier=1.0):
        self.id = key_id
        self.label = label
        self.width_multiplier = width_multiplier
        
        # Bounding box dynamically populated by Manager
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        
        # Supported States: "idle", "hover", "selected", "disabled", "suggested", "progressing", "ready", "intent_target"
        self.state = "idle"
        self.hover_confidence = 0.0

    def update_state(self, new_state):
        valid_states = ["idle", "hover", "selected", "disabled", "suggested", "progressing", "ready", "intent_target"]
        if new_state in valid_states:
            self.state = new_state

    def check_hit(self, px, py):
        """Returns True if the (px, py) coordinate is inside this key."""
        return (self.x <= px <= self.x + self.w) and (self.y <= py <= self.y + self.h)

    def draw(self, frame):
        # Professional Color Palette (BGR format)
        colors = {
            "idle": ((230, 230, 230), (50, 50, 50)),         # light gray bg, dark text
            "hover": ((200, 200, 255), (0, 0, 0)),           # slight blue tint bg
            "intent_target": ((230, 240, 255), (20, 20, 150)),# very faint blue highlight for predicted intent
            "progressing": ((180, 220, 255), (0, 0, 0)),     # light blue building up
            "ready": ((100, 255, 100), (0, 50, 0)),          # stable green ready to blink
            "selected": ((255, 150, 50), (255, 255, 255)),   # blue/orange pop
            "disabled": ((100, 100, 100), (180, 180, 180)),  # dim
            "suggested": ((150, 255, 150), (0, 0, 0))        # green hint for AI predictions
        }
        
        bg_col, txt_col = colors.get(self.state, colors["idle"])

        # Create glassmorphism overlay using clone
        overlay = frame.copy()
        
        # Draw rounded rectangle (simulated with cv2 by drawing a normal rect as base)
        # Using a solid rectangle for now, can be replaced with custom rounded corner logic
        cv2.rectangle(overlay, (self.x, self.y), (self.x + self.w, self.y + self.h), bg_col, -1)
        
        # Apply alpha blend
        # Progressing gets less transparent
        alpha_map = {"idle": 0.85, "intent_target": 0.85, "hover": 0.90, "progressing": 0.95, "ready": 1.0, "selected": 1.0, "disabled": 0.7}
        alpha = alpha_map.get(self.state, 0.85)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Border
        border_col = (180, 180, 180) 
        thickness = 1
        if self.state in ["hover", "intent_target", "progressing"]:
            thickness = 2
            border_col = (100, 150, 255)
        elif self.state in ["ready", "selected"]:
            thickness = 2
            border_col = (255, 255, 255)
            
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h), border_col, thickness)

        # Progress Bar
        if self.hover_confidence > 0:
            bar_w = int(self.w * self.hover_confidence)
            # Draw a thick green bar along the bottom
            cv2.rectangle(frame, (self.x, self.y + self.h - 5), (self.x + bar_w, self.y + self.h), (0, 200, 0), -1)

        # Center Text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6 if len(self.label) > 1 else 0.8
        thickness = 2
        
        text_size = cv2.getTextSize(self.label, font, font_scale, thickness)[0]
        text_x = self.x + (self.w - text_size[0]) // 2
        text_y = self.y + (self.h + text_size[1]) // 2
        
        cv2.putText(frame, self.label, (text_x, text_y), font, font_scale, txt_col, thickness, cv2.LINE_AA)
