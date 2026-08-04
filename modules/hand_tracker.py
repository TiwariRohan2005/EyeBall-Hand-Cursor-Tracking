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

        hand_data = None
        landmarks_list = None

        if result.hand_landmarks and result.handedness:
            h, w, _ = frame.shape

            landmarks_list = result.hand_landmarks[0]
            landmark = landmarks_list[8]   # index fingertip
            confidence = result.handedness[0][0].score

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            hand_data = ((x, y), confidence)

            cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)

        return frame, hand_data, landmarks_list