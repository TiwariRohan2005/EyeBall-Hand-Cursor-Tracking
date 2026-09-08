import cv2
import time
from modules.eye_tracker import EyeTracker
from modules.mouse_actions import MouseController
from modules.hand_tracker import HandTracker
from modules.ai_processor import CursorStabilizer
from modules.gesture_engine import GestureEngine
from modules.auth import AuthManager
from modules.evaluation import EvaluationManager
from modules.context import ContextAnalyzer, IntentEngine

def start_ai_loop(frame_queue, is_running_cb):
    cap = cv2.VideoCapture(0)

    eye_tracker = EyeTracker()
    hand_tracker = HandTracker()
    stabilizer = CursorStabilizer()
    gesture_engine = GestureEngine()
    mouse = MouseController()
    auth_manager = AuthManager()

    if not auth_manager.users:
        print("\n[!] No registered users found. Run the Calibration Wizard first.")
        return

    adaptive_engine = None
    eval_manager = EvaluationManager()
    context_analyzer = ContextAnalyzer()
    intent_engine = IntentEngine()

    while is_running_cb():
        loop_start_time = time.perf_counter()
        
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        frame, eye_status, auth_landmarks = eye_tracker.process(frame)
        frame, hand_data, landmarks = hand_tracker.process(frame)
        
        switched = context_analyzer.update()
        if switched:
            eval_manager.log_metric("context", {"app": context_analyzer.current_app, "mode": context_analyzer.current_mode})
                
        auth_state, current_uid, auth_conf = auth_manager.process_face(auth_landmarks)
        
        if auth_state == "AUTHENTICATED":
            if not adaptive_engine or adaptive_engine.username != auth_manager.current_user:
                from modules.calibration import AdaptiveLearningEngine
                adaptive_engine = AdaptiveLearningEngine(auth_manager.current_user)
                eye_tracker.adaptive_engine = adaptive_engine
                stabilizer.adaptive_engine = adaptive_engine
                
        eval_manager.log_metric("auth", {
            "state": auth_state,
            "confidence": auth_conf,
            "user": auth_manager.current_user
        })
        
        if auth_state == "LOCKED" or auth_state == "AUTHENTICATING":
            cv2.putText(frame, "SYSTEM LOCKED. Identity Verification Required.", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(frame, f"Match Confidence: {auth_conf:0.2f}", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        elif auth_state == "AUTHENTICATED":
            cv2.putText(frame, f"Identity Verified: {auth_manager.current_user} ({auth_conf:0.2f})", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        gesture, gesture_conf = gesture_engine.process(landmarks)
        
        if auth_state == "AUTHENTICATED":
            intent = intent_engine.evaluate(context_analyzer.current_mode, gesture)
            
            final_intent = eye_status
            if intent != "NONE":
                final_intent = intent

            if gesture == "INDEX_POINT" or final_intent == "CURSOR_MOVE":
                smoothed_pos = stabilizer.process(hand_data)
                if smoothed_pos and hand_data:
                    import math
                    raw_x, raw_y = hand_data[0]
                    variance = math.hypot(raw_x - smoothed_pos[0], raw_y - smoothed_pos[1])
                    eval_manager.log_metric("cursor", {
                        "raw_x": raw_x, "raw_y": raw_y,
                        "smooth_x": smoothed_pos[0], "smooth_y": smoothed_pos[1],
                        "variance": variance
                    })
            else:
                smoothed_pos = None

            mouse.handle(final_intent, smoothed_pos, frame.shape)
        
        display_text = f"App: {context_analyzer.current_app.capitalize()} | Mode: {context_analyzer.current_mode}"
        cv2.putText(frame, display_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        loop_end_time = time.perf_counter()
        latency_ms = (loop_end_time - loop_start_time) * 1000
        eval_manager.log_metric("latency", {"latency_ms": latency_ms})
        
        # Async Video Dispatch directly to Tkinter GUI thread!
        payload = {
            "frame": frame,
            "stats": {
                "latency": latency_ms,
                "auth_state": auth_state,
                "context_mode": context_analyzer.current_mode
            }
        }
        try:
            frame_queue.put_nowait(payload)
        except getattr(queue, 'Full', Exception):
            pass

    auth_manager.lock_session("App exited")
    if adaptive_engine:
        print("\n[~] Saving learned adaptive kinematics profile for next session...")
        adaptive_engine.save()
        
    print("\n[~] Halting Telemetry Queue...")
    eval_manager.shutdown_and_export()
        
    if hasattr(eye_tracker, 'face_mesh'):
        eye_tracker.face_mesh.close()
    if hasattr(hand_tracker, 'detector'):
        hand_tracker.detector.close()
    cap.release()
