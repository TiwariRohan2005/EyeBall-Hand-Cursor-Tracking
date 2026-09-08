from .config_manager import AdaptiveConfig

class CalibrationEngine:
    def __init__(self):
        self.left_ears = []
        self.right_ears = []
        
        # Environmental
        self.lighting_samples = []
    
    def process_frame(self, frame, face_landmarks, h, w):
        """
        Called 30 times during user registration to extract baseline physical variables.
        """
        import math
        import cv2
        import numpy as np
        
        def dist(p1, p2):
            return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

        # 1. Lighting analysis (Grayscale Mean)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        self.lighting_samples.append(mean_brightness)

        if not face_landmarks:
            return
            
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks]
        
        # 2. Eye Aspect Ratio Extraction
        # Left eye: top=159, bottom=145, left=33, right=133
        v_left = dist(pts[159], pts[145])
        h_left = dist(pts[33], pts[133])
        left_ratio = v_left / h_left if h_left else 0
        
        # Right eye: top=386, bottom=374, left=362, right=263
        v_right = dist(pts[386], pts[374])
        h_right = dist(pts[362], pts[263])
        right_ratio = v_right / h_right if h_right else 0
        
        self.left_ears.append(left_ratio)
        self.right_ears.append(right_ratio)

    def finalize_calibration(self) -> dict:
        """
        Finishes calibration and exports normalized tuning limits.
        Discards outliers (accidental blinks) to calculate the true 'Resting Eye state'.
        """
        import numpy as np

        def filter_outliers(data):
            if not data: return 0.25
            arr = np.array(data)
            q1, q3 = np.percentile(arr, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            # Only keeping values above lower bound (filtering natural blinks during registration)
            filtered = arr[arr > lower_bound]
            return np.mean(filtered) if len(filtered) > 0 else np.mean(arr)

        baseline_left = float(filter_outliers(self.left_ears))
        baseline_right = float(filter_outliers(self.right_ears))
        avg_lighting = float(np.mean(self.lighting_samples)) if self.lighting_samples else 128.0

        # Create a fresh scalable config attached specifically to this user
        config = AdaptiveConfig()
        
        # Example dynamic scaling: If lighting is incredibly dark (avg < 50), 
        # computer vision logic stutters, so we artificially expand the stability radius tolerance
        if avg_lighting < 50.0:
            config.stability_radius *= 1.25 # Give them 25% more leniency in the dark

        return {
            "baseline_left_ear": baseline_left,
            "baseline_right_ear": baseline_right,
            "avg_lighting": avg_lighting,
            "adaptive_config": config.to_dict()
        }
