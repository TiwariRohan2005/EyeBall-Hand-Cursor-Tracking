import math
import numpy as np

class FaceRecognizer:
    def __init__(self):
        # Cosine similarity threshold for verification
        self.threshold = 0.995 

    def _dist(self, p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def extract_embedding(self, face_landmarks):
        pts = face_landmarks
        
        # We need a stable base metric to normalize against head rotation/scale.
        # Outer eye corners
        left_eye_outer = pts[33]
        right_eye_outer = pts[263]
        scale = self._dist(left_eye_outer, right_eye_outer)
        
        if scale == 0:
            return None

        # Key facial topology distances acting as our geometric identity matrix
        features = [
            self._dist(pts[10], pts[152]), # Top of head to chin
            self._dist(pts[234], pts[454]), # Width of face
            self._dist(pts[168], pts[4]),   # Nose bridge
            self._dist(pts[61], pts[291]),  # Mouth width
            self._dist(pts[0], pts[17]),    # Mouth height
            self._dist(pts[130], pts[359]), # Inner eye distance
            self._dist(pts[280], pts[152]), # Right cheek to chin
            self._dist(pts[50], pts[152]),  # Left cheek to chin
            self._dist(pts[195], pts[94]),  # Nose width
            self._dist(pts[13], pts[14]),   # Lip thickness
        ]
        
        # Normalize
        normalized = np.array(features, dtype=np.float32) / scale
        
        # L2 normalize the vector
        norm = np.linalg.norm(normalized)
        if norm > 0:
            normalized = normalized / norm
            
        return normalized.tolist()

    def compare(self, emb1, emb2):
        if not emb1 or not emb2: return 0.0
        # Cosine similarity
        v1 = np.array(emb1)
        v2 = np.array(emb2)
        dot = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        return float(dot / (norm_v1 * norm_v2))
