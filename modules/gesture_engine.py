import math
import time

class GestureEngine:
    def __init__(self):
        self.history = []
        self.history_size = 3
        
        self.last_gesture = "UNKNOWN"
        self.last_action_time = 0
        
        # Cooldowns in seconds for discrete repetitive actions
        self.cooldowns = {
            "PINCH": 0.5,
            "TWO_FINGERS": 0.5,
            "THREE_FINGERS": 0.5,
            "FIVE_FINGERS": 1.0,
            "FIST": 0.2
        }

    def _dist(self, p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def get_finger_states(self, landmarks):
        # MediaPipe Landmarks: 
        # 0: wrist
        # Thumb: 1-4, Index: 5-8, Middle: 9-12, Ring: 13-16, Pinky: 17-20
        # DIP joints: 7, 11, 15, 19. PIP joints: 6, 10, 14, 18
        states = {}
        wrist = landmarks[0]
        
        # Index, Middle, Ring, Pinky: extended if tip is further from wrist than PIP joint
        states['index'] = self._dist(landmarks[8], wrist) > self._dist(landmarks[6], wrist)
        states['middle'] = self._dist(landmarks[12], wrist) > self._dist(landmarks[10], wrist)
        states['ring'] = self._dist(landmarks[16], wrist) > self._dist(landmarks[14], wrist)
        states['pinky'] = self._dist(landmarks[20], wrist) > self._dist(landmarks[18], wrist)
        
        # Thumb: check if tip is further from pinky MCP than thumb MCP
        states['thumb'] = self._dist(landmarks[4], landmarks[17]) > self._dist(landmarks[2], landmarks[17])
        
        # Pinch validation: exact distance between thumb tip(4) and index tip(8)
        pinch_dist = self._dist(landmarks[4], landmarks[8])
        # Normalized threshold - 0.05 is generally very close
        is_pinch = pinch_dist < 0.05
        
        return states, is_pinch

    def recognize(self, states, is_pinch):
        # FIST: all fingers curled
        if not states['index'] and not states['middle'] and not states['ring'] and not states['pinky']:
            return "FIST"
            
        # PINCH: precisely thumb + index touching, others folded
        if is_pinch and not states['middle'] and not states['ring'] and not states['pinky']:
            return "PINCH"
            
        # FIVE FINGERS: all open
        if states['thumb'] and states['index'] and states['middle'] and states['ring'] and states['pinky']:
            return "FIVE_FINGERS"
            
        # THREE FINGERS: Index + Middle + Ring
        if states['index'] and states['middle'] and states['ring'] and not states['pinky']:
            return "THREE_FINGERS"
            
        # TWO FINGERS: Index + Middle
        if states['index'] and states['middle'] and not states['ring'] and not states['pinky']:
            return "TWO_FINGERS"
            
        # INDEX POINT: only index extended (Cursor movement)
        if states['index'] and not states['middle'] and not states['ring'] and not states['pinky']:
            return "INDEX_POINT"
            
        return "UNKNOWN"

    def process(self, landmarks):
        if not landmarks:
            self.history.clear()
            return "UNKNOWN", 0.0

        states, is_pinch = self.get_finger_states(landmarks)
        raw_gesture = self.recognize(states, is_pinch)
        
        self.history.append(raw_gesture)
        if len(self.history) > self.history_size:
            self.history.pop(0)
            
        # Temporal Validation: Gesture must be perfectly stable for N frames
        if len(self.history) == self.history_size and all(g == raw_gesture for g in self.history):
            validated_gesture = raw_gesture
        else:
            validated_gesture = "UNKNOWN"
            
        # Cooldown Validation
        now = time.time()
        # We only apply cooldown to discrete clicks/actions, NOT continuous ones like INDEX_POINT
        if validated_gesture not in ["UNKNOWN", "INDEX_POINT"]:
            cooldown = self.cooldowns.get(validated_gesture, 0.5)
            
            # If the user holds the gesture, we check against last execution
            if validated_gesture == self.last_gesture:
                if now - self.last_action_time < cooldown:
                    validated_gesture = "UNKNOWN"  # Suppress repeat
                else:
                    self.last_action_time = now # Re-fire allowed
            else:
                self.last_action_time = now
                
        self.last_gesture = validated_gesture if validated_gesture != "UNKNOWN" else self.last_gesture
        
        # Confidence score (placeholder based on stability)
        confidence = 1.0 if validated_gesture != "UNKNOWN" else 0.0
        
        return validated_gesture, confidence
