import cv2
import mediapipe as mp
import time
import math
from mediapipe.tasks.python import BaseOptions
from collections import Counter

class LibraryGestureEngine:
    def __init__(self, model_asset_path="hand_landmarker.task"):
        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(
            mp.tasks.vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_asset_path),
                num_hands=2
            )
        )
        
        self.hand_x_history = {}
        self.history_size = 5
        self.swipe_threshold = 0.15
        
        self.last_action_time = time.time()
        self.cooldown = 1.0
        
        # Pointing State Machine
        self.pointing_state = "NONE"
        self.pointing_start_time = 0.0
        self.is_continuous = False
        
        self.pointing_config = {
            "dom_threshold": 1.1,
            "hold_seconds": 2.0,
            "deadzone_dist": 0.05
        }
        self.pointing_history = []
        
    def _is_thumb_up(self, landmarks):
        thumb_tip_y = landmarks[4].y
        index_pip_y = landmarks[6].y
        middle_pip_y = landmarks[10].y
        if thumb_tip_y < index_pip_y - 0.05 and thumb_tip_y < middle_pip_y - 0.05:
            index_folded = landmarks[8].y > landmarks[6].y
            middle_folded = landmarks[12].y > landmarks[10].y
            if index_folded and middle_folded:
                return True
        return False
        
    def _is_thumb_down(self, landmarks):
        thumb_tip_y = landmarks[4].y
        index_pip_y = landmarks[6].y
        middle_pip_y = landmarks[10].y
        if thumb_tip_y > index_pip_y + 0.05 and thumb_tip_y > middle_pip_y + 0.05:
            index_folded = landmarks[8].y < landmarks[6].y or landmarks[8].y > landmarks[5].y
            if index_folded:
                return True
        return False
        
    def _get_pointing_direction(self, landmarks):
        wrist = landmarks[0]
        fingers = [
            (5, 8),   # Index
            (9, 12),  # Middle
            (13, 16), # Ring
            (17, 20)  # Pinky
        ]
        
        max_dist = 0
        best_finger = None
        
        for mcp_idx, tip_idx in fingers:
            tip = landmarks[tip_idx]
            pip = landmarks[mcp_idx+1]
            mcp = landmarks[mcp_idx]
            
            d_tip = math.hypot(tip.x - wrist.x, tip.y - wrist.y)
            d_pip = math.hypot(pip.x - wrist.x, pip.y - wrist.y)
            
            if d_tip > d_pip + 0.03: 
                if d_tip > max_dist:
                    max_dist = d_tip
                    best_finger = (mcp, tip)
                    
        if best_finger:
            mcp, tip = best_finger
            dx = tip.x - mcp.x
            dy = tip.y - mcp.y
            
            # Deadzone
            if math.hypot(dx, dy) < self.pointing_config["deadzone_dist"]:
                return "NONE"
                
            if abs(dx) > abs(dy) * self.pointing_config["dom_threshold"]:
                return "POINT_LEFT" if dx < 0 else "POINT_RIGHT"
            elif abs(dy) > abs(dx) * self.pointing_config["dom_threshold"]:
                return "POINT_UP" if dy < 0 else "POINT_DOWN"
                
        return "NONE"

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect(mp_image)
        
        detected_gesture = None
        self.is_continuous = False
        now = time.time()
        
        if result.hand_landmarks and result.handedness:
            thumbs_up_count = 0
            thumbs_down_count = 0
            raw_point = "NONE"
            
            for idx, hand_marks in enumerate(result.hand_landmarks):
                wrist_x = hand_marks[0].x
                if idx not in self.hand_x_history:
                    self.hand_x_history[idx] = []
                self.hand_x_history[idx].append(wrist_x)
                if len(self.hand_x_history[idx]) > self.history_size:
                    self.hand_x_history[idx].pop(0)

                if self._is_thumb_up(hand_marks):
                    thumbs_up_count += 1
                elif self._is_thumb_down(hand_marks):
                    thumbs_down_count += 1
                else:
                    pt_dir = self._get_pointing_direction(hand_marks)
                    if pt_dir != "NONE":
                        raw_point = pt_dir
                        
            # Precedence
            if thumbs_up_count == 2: detected_gesture = "BOTH_THUMBS_UP"
            elif thumbs_down_count == 2: detected_gesture = "BOTH_THUMBS_DOWN"
            elif thumbs_up_count == 1: detected_gesture = "RIGHT_THUMB_UP"
            elif thumbs_down_count == 1: detected_gesture = "RIGHT_THUMB_DOWN"
            else:
                self.pointing_history.append(raw_point)
                if len(self.pointing_history) > 3: self.pointing_history.pop(0)
                
                stable_point = Counter(self.pointing_history).most_common(1)[0][0]
                
                if stable_point != "NONE":
                    if self.pointing_state != stable_point:
                        self.pointing_state = stable_point
                        self.pointing_start_time = now
                    else:
                        hold_duration = now - self.pointing_start_time
                        self.is_continuous = (hold_duration >= self.pointing_config["hold_seconds"])
                    detected_gesture = self.pointing_state
                else:
                    self.pointing_state = "NONE"

                if detected_gesture is None:
                    # check swipe
                    for idx, xs in self.hand_x_history.items():
                        if len(xs) == self.history_size:
                            dx = xs[-1] - xs[0]
                            if dx > self.swipe_threshold:
                                detected_gesture = "SWIPE_RIGHT"
                                self.hand_x_history[idx].clear()
                                break
                            elif dx < -self.swipe_threshold:
                                detected_gesture = "SWIPE_LEFT"
                                self.hand_x_history[idx].clear()
                                break
        else:
            self.pointing_state = "NONE"
            self.pointing_history.clear()
            
        # Cooldown management
        if detected_gesture:
            is_directional = detected_gesture in ["POINT_LEFT", "POINT_RIGHT", "POINT_UP", "POINT_DOWN"]
            if is_directional:
                if self.is_continuous:
                    # 0.3 seconds repeat delay for continuous book selection
                    if now - self.last_action_time > 0.30:
                        self.last_action_time = now
                    else:
                        detected_gesture = None
                else:
                    if now - self.last_action_time > 0.15:
                        self.last_action_time = now
                    else:
                        detected_gesture = None
            else:
                if now - self.last_action_time > self.cooldown:
                    self.last_action_time = now
                else:
                    detected_gesture = None
        else:
             self.pointing_state = "NONE"
             
        return frame, detected_gesture
