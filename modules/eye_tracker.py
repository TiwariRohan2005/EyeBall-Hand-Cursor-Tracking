import cv2
import math
import time
from mediapipe.tasks.python import BaseOptions
import mediapipe as mp

class EyeTracker:
    def __init__(self, adaptive_engine=None):
        self.last_action = 0

        self.face_mesh = mp.tasks.vision.FaceLandmarker.create_from_options(
            mp.tasks.vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path="face_landmarker.task"),
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1
            )
        )
        
        self.adaptive_engine = adaptive_engine
        
        self.left_closed_start = 0
        self.right_closed_start = 0
        self.both_closed_start = 0

    def eye_ratio(self, top, bottom, left, right):
        vertical = math.dist(top, bottom)
        horizontal = math.dist(left, right)
        return vertical / horizontal if horizontal else 0

    def process(self, frame):
        status = "Tracking"

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self.face_mesh.detect(mp_image)

        face_landmarks_out = None
        if result.face_landmarks:
            face_landmarks_out = result.face_landmarks[0]
            h, w, _ = frame.shape
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in result.face_landmarks[0]]

            left_ratio = self.eye_ratio(pts[159], pts[145], pts[33], pts[133])
            right_ratio = self.eye_ratio(pts[386], pts[374], pts[362], pts[263])
            
            # Load adaptive baselines and limits dynamically
            from modules.calibration.config_manager import AdaptiveConfig
            if self.adaptive_engine:
                baseline_left, baseline_right = self.adaptive_engine.get_baseline_ears()
                config = self.adaptive_engine.get_config()
            else:
                baseline_left, baseline_right = 0.28, 0.28  # Safe universal defaults
                config = AdaptiveConfig()

            now = time.time()
            
            left_closed = left_ratio < (baseline_left * config.blink_threshold_ratio)
            right_closed = right_ratio < (baseline_right * config.blink_threshold_ratio)
            
            # State tracking
            if left_closed and not right_closed:
                if self.left_closed_start == 0:
                    self.left_closed_start = now
                self.right_closed_start = 0
                self.both_closed_start = 0
                
            elif right_closed and not left_closed:
                if self.right_closed_start == 0:
                    self.right_closed_start = now
                self.left_closed_start = 0
                self.both_closed_start = 0
                
            elif left_closed and right_closed:
                if self.both_closed_start == 0:
                    self.both_closed_start = now
                self.left_closed_start = 0
                self.right_closed_start = 0
                
                if now - self.both_closed_start > 1.0: # Pause threshold
                    status = "PAUSE"
            else:
                # Eyes are open. Process triggers if recently closed appropriately.
                if self.left_closed_start > 0:
                    duration = now - self.left_closed_start
                    if config.min_blink_time < duration < config.max_blink_time and now - self.last_action > 1:
                        status = "LEFT_CLICK"
                        self.last_action = now
                        if self.adaptive_engine: self.adaptive_engine.adapt_blink_timing(felt_fatigued=False)
                    elif duration >= config.max_blink_time:    
                        if self.adaptive_engine: self.adaptive_engine.adapt_blink_timing(felt_fatigued=True)
                        
                if self.right_closed_start > 0:
                    duration = now - self.right_closed_start
                    if config.min_blink_time < duration < config.max_blink_time and now - self.last_action > 1:
                        status = "RIGHT_CLICK"
                        self.last_action = now

                self.left_closed_start = 0
                self.right_closed_start = 0
                self.both_closed_start = 0

        else:
            status = "No face detected"

        return frame, status, face_landmarks_out
