from .keys import Key

class VirtualKeyboardManager:
    def __init__(self):
        self.keys = []
        self._build_layout()

    def _build_layout(self):
        """Builds a modern QWERTY layout assigning spatial logic and unique IDs."""
        layout_map = [
            [("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("Backspace", 2)],
            [("Tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1), ("]", 1), ("\\", 1)],
            [("Caps", 1.8), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1), ("Enter", 1.8)],
            [("Shift", 2.2), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("Shift", 2.2)],
            [("Sym", 1.5), ("Space", 7), ("Clear", 1.5)]
        ]

        self.keys = []
        for r, row in enumerate(layout_map):
            for c, (label, width_mult) in enumerate(row):
                key_id = f"K_R{r}_C{c}_{label}"
                self.keys.append(Key(key_id, label, width_mult))

    def calculate_bounds(self, frame_w, frame_h):
        """
        Dynamically calculates the pixel (x,y,w,h) values for every key so that 
        the keyboard naturally scales to the bottom half of any camera resolution.
        """
        if not self.keys: return

        # Place keyboard at the bottom 40% of the screen
        kb_h = int(frame_h * 0.4)
        kb_y = frame_h - kb_h
        
        # Horizontal margins
        margin_x = int(frame_w * 0.05)
        usable_w = frame_w - (margin_x * 2)
        
        # We have 5 rows. Add some gap between rows and columns
        gap = 5
        row_h = (kb_h - (gap * 6)) // 5
        
        # Reconstruct rows to tally width multipliers
        # This matches the layout indices implicitly
        rows = [[] for _ in range(5)]
        for k in self.keys:
            r_idx = int(k.id.split("_")[1][1:]) # Extracted from K_R0..
            rows[r_idx].append(k)

        current_y = kb_y + gap
        
        for r_idx, row_keys in enumerate(rows):
            total_mult = sum(k.width_multiplier for k in row_keys)
            
            # Width of a standard '1.0' key on this row
            unit_w = (usable_w - (gap * (len(row_keys) - 1))) / total_mult
            
            current_x = margin_x
            for k in row_keys:
                k.w = int(unit_w * k.width_multiplier)
                k.h = row_h
                k.x = current_x
                k.y = current_y
                
                current_x += k.w + gap
            
            current_y += row_h + gap

    def render(self, frame):
        """Renders the entire keyboard onto the provided OpenCV frame."""
        # Lazily calculate bounds if first time or resolution changed
        h, w, _ = frame.shape
        if self.keys and (self.keys[0].w == 0 or frame.shape[1] != w):
            self.calculate_bounds(w, h)
            
        for k in self.keys:
            k.draw(frame)
            
        return frame

    # ====================================================
    # PUBLIC APIS FOR PHASE 2 (AI PIPELINE INTEGRATION)
    # ====================================================

    def handle_hover(self, cursor_x, cursor_y):
        """
        Gesture Engine API: Call with real-time hand/mouse coordinates.
        Sets the intersecting key to 'hover' and rests others to 'idle'.
        """
        for k in self.keys:
            if k.state in ["disabled", "suggested", "selected"]:
                continue # Do not override locked/suggested states automatically
                
            if k.check_hit(cursor_x, cursor_y):
                k.update_state("hover")
            elif k.state == "hover":
                k.update_state("idle")

    def confirm_selection(self, cursor_x, cursor_y):
        """
        Eye Tracker API: Call when blink trigger is detected.
        Locks the target key into 'selected' momentarily and returns the key.
        """
        for k in self.keys:
            if k.state != "disabled" and k.check_hit(cursor_x, cursor_y):
                k.update_state("selected")
                return k
        return None

    def highlight_predictions(self, suggested_labels):
        """
        Prediction Engine API: Feeds a list of likely next characters.
        """
        for k in self.keys:
            if k.state not in ["disabled", "selected"]:
                if k.label.upper() in [l.upper() for l in suggested_labels]:
                    k.update_state("suggested")
                else:
                    k.update_state("idle")

    def set_global_state(self, locked=False):
        """
        Auth Engine API: Locks out the keyboard if Authentication drops.
        """
        state = "disabled" if locked else "idle"
        for k in self.keys:
            k.update_state(state)
