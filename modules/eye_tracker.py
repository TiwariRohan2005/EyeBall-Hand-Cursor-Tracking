import cv2
import math
import time
from mediapipe.tasks.python import BaseOptions
import mediapipe as mp

class EyeTracker:
    def __init__(self):
        self.last_action = 0

        self.face_mesh = mp.tasks.vision.FaceLandmarker.create_from_options(
            mp.tasks.vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path="face_landmarker.task"),
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1
            )
        )
        
        self.calibrating = True
        self.calibration_frames = 30
        self.frame_count = 0
        self.left_ears = []
        self.right_ears = []
        
        self.baseline_left = 0
        self.baseline_right = 0
        
        self.left_closed_start = 0
        self.right_closed_start = 0
        self.both_closed_start = 0
        
        # Adaptive threshold: 65% of baseline EAR
        self.closure_threshold_ratio = 0.65
        
        # Temporal settings
        self.min_blink_time = 0.15
        self.max_blink_time = 0.8
        self.pause_time = 1.0

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
            
            if self.calibrating:
                self.left_ears.append(left_ratio)
                self.right_ears.append(right_ratio)
                self.frame_count += 1
                
                status = f"CALIBRATING ({self.frame_count}/{self.calibration_frames})"
                
                if self.frame_count >= self.calibration_frames:
                    # Use 80th percentile to discard accidental blinks during calibration
                    sorted_left = sorted(self.left_ears)
                    sorted_right = sorted(self.right_ears)
                    idx = int(self.calibration_frames * 0.8)
                    
                    self.baseline_left = sorted_left[idx]
                    self.baseline_right = sorted_right[idx]
                    self.calibrating = False
                    
                return frame, status, face_landmarks_out

            now = time.time()
            
            left_closed = left_ratio < (self.baseline_left * self.closure_threshold_ratio)
            right_closed = right_ratio < (self.baseline_right * self.closure_threshold_ratio)
            
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
                
                if now - self.both_closed_start > self.pause_time:
                    status = "PAUSE"
            else:
                # Eyes are open. Process triggers if recently closed appropriately.
                if self.left_closed_start > 0:
                    duration = now - self.left_closed_start
                    if self.min_blink_time < duration < self.max_blink_time and now - self.last_action > 1:
                        status = "LEFT_CLICK"
                        self.last_action = now
                        
                if self.right_closed_start > 0:
                    duration = now - self.right_closed_start
                    if self.min_blink_time < duration < self.max_blink_time and now - self.last_action > 1:
                        status = "RIGHT_CLICK"
                        self.last_action = now

                self.left_closed_start = 0
                self.right_closed_start = 0
                self.both_closed_start = 0

        else:
            if self.calibrating:
                status = "CALIBRATING (No face detected)"

        return frame, status, face_landmarks_out
