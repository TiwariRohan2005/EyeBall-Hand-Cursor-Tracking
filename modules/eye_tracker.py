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

    def eye_ratio(self, top, bottom, left, right):
        vertical = math.dist(top, bottom)
        horizontal = math.dist(left, right)
        return vertical / horizontal if horizontal else 0

    def process(self, frame):
        status = "Tracking"

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self.face_mesh.detect(mp_image)

        if result.face_landmarks:
            h, w, _ = frame.shape
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in result.face_landmarks[0]]

            left_ratio = self.eye_ratio(pts[159], pts[145], pts[33], pts[133])
            right_ratio = self.eye_ratio(pts[386], pts[374], pts[362], pts[263])

            now = time.time()

            if left_ratio < 0.18 and right_ratio > 0.20 and now - self.last_action > 1:
                status = "LEFT_CLICK"
                self.last_action = now

            elif right_ratio < 0.18 and left_ratio > 0.20 and now - self.last_action > 1:
                status = "RIGHT_CLICK"
                self.last_action = now

            elif left_ratio < 0.18 and right_ratio < 0.18:
                status = "PAUSE"

        return frame, status
