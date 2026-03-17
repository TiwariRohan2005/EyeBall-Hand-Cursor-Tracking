import cv2
import mediapipe as mp

from mediapipe.tasks.python import BaseOptions


class HandTracker:
    def __init__(self):
        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(
            mp.tasks.vision.HandLandmarkerOptions(
                base_options=BaseOptions(
                    model_asset_path="hand_landmarker.task"
                ),
                num_hands=1
            )
        )

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.detector.detect(mp_image)

        hand_pos = None

        if result.hand_landmarks:
            h, w, _ = frame.shape

            landmark = result.hand_landmarks[0][8]   # index fingertip

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            hand_pos = (x, y)

            cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)

        return frame, hand_pos