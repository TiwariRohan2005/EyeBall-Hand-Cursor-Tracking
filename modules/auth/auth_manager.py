import time
from .logger import AuthLogger
from .storage import UserStorage
from .face_recognizer import FaceRecognizer

class AuthManager:
    def __init__(self, mode="AUTHENTICATING", target_user_id=None):
        self.logger = AuthLogger()
        self.storage = UserStorage()
        self.recognizer = FaceRecognizer()
        
        self.users = self.storage.get_all_users()
        
        self.state = mode
        self.target_user_id = target_user_id
        
        self.enrollment_samples = []
        self.enrollment_target = 30
        
        self.current_user = None
        self.session_start = 0
        
        self.fail_frames = 0
        self.max_fail_frames = 15 # lock if no face for 15 frames
        self.last_confidence = 0.0

    def process_face(self, face_landmarks):
        if not face_landmarks:
            self.fail_frames += 1
            if self.state == "AUTHENTICATED" and self.fail_frames > self.max_fail_frames:
                self.lock_session("Face disappeared")
            return self.state, self.current_user, self.last_confidence
            
        self.fail_frames = 0
        emb = self.recognizer.extract_embedding(face_landmarks)
        if not emb:
            return self.state, self.current_user, self.last_confidence

        if self.state == "ENROLLING":
            self.enrollment_samples.append(emb)
            if len(self.enrollment_samples) >= self.enrollment_target:
                # Average embedding
                avg_emb = [sum(x)/len(x) for x in zip(*self.enrollment_samples)]
                user_id = self.target_user_id if self.target_user_id else f"User_{len(self.users) + 1}"
                self.storage.add_user(user_id, {"embedding": avg_emb})
                self.users = self.storage.get_all_users()
                self.logger.logger.info(f"New user enrolled: {user_id}")
                self.state = "ENROLLMENT_COMPLETE"
            self.last_confidence = len(self.enrollment_samples) / self.enrollment_target
                
        elif self.state == "AUTHENTICATING":
            best_match = None
            best_score = 0
            for uid, profile in self.users.items():
                score = self.recognizer.compare(emb, profile["embedding"])
                if score > best_score:
                    best_score = score
                    best_match = uid
                    
            if best_match and best_score > self.recognizer.threshold:
                self.start_session(best_match)
                self.last_confidence = best_score
            else:
                self.last_confidence = best_score
                self.logger.failed_auth("No user matched")
                
        elif self.state == "AUTHENTICATED":
            # Continuous verification
            profile = self.users[self.current_user]
            score = self.recognizer.compare(emb, profile["embedding"])
            self.last_confidence = score
            
            if score < self.recognizer.threshold:
                self.logger.unauthorized_attempt()
                self.lock_session(f"Confidence dropped: {score:.2f}")

        elif self.state == "LOCKED":
             # Auto-unlock attempt
             best_match = None
             best_score = 0
             for uid, profile in self.users.items():
                 score = self.recognizer.compare(emb, profile["embedding"])
                 if score > best_score:
                     best_score = score
                     best_match = uid
             if best_match and best_score > self.recognizer.threshold:
                 self.start_session(best_match)
                 self.last_confidence = best_score
             else:
                 self.last_confidence = best_score

        return self.state, self.current_user, self.last_confidence

    def start_session(self, user_id):
        self.current_user = user_id
        self.state = "AUTHENTICATED"
        self.session_start = time.time()
        self.logger.login(user_id)

    def lock_session(self, reason="Manual"):
        if self.state == "AUTHENTICATED" and self.current_user:
            duration = time.time() - self.session_start
            self.logger.logout(self.current_user, duration)
        self.current_user = None
        self.state = "LOCKED"
