import cv2
from modules.eye_tracker import EyeTracker
from modules.mouse_actions import MouseController
from modules.hand_tracker import HandTracker
from modules.ai_processor import CursorStabilizer
from modules.gesture_engine import GestureEngine
from modules.auth import AuthManager

cap = cv2.VideoCapture(0)

eye_tracker = EyeTracker()
hand_tracker = HandTracker()
stabilizer = CursorStabilizer()
gesture_engine = GestureEngine()
mouse = MouseController()
auth_manager = AuthManager()

if not auth_manager.users:
    print("\n[!] No registered users found. The application cannot start.")
    print("    Please run 'python register.py' to enroll your face first.\n")
    import sys
    sys.exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    frame, eye_status, auth_landmarks = eye_tracker.process(frame)
    frame, hand_data, landmarks = hand_tracker.process(frame)
            
    auth_state, auth_conf = auth_manager.process_face(auth_landmarks)
    
    # Render Auth state prominently
    if auth_state == "LOCKED" or auth_state == "AUTHENTICATING":
        cv2.putText(frame, "SYSTEM LOCKED. Identity Verification Required.", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(frame, f"Match Confidence: {auth_conf:0.2f}", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    elif auth_state == "AUTHENTICATED":
        cv2.putText(frame, f"Identity Verified: {auth_manager.current_user} ({auth_conf:0.2f})", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Core interaction routing
    gesture, gesture_conf = gesture_engine.process(landmarks)
    
    if auth_state == "AUTHENTICATED":
        # Priority: Gesture overrides eye_status if gesture implies a click or action
        final_status = eye_status
        if gesture == "PINCH":
            final_status = "LEFT_CLICK"
        elif gesture == "TWO_FINGERS":
            final_status = "RIGHT_CLICK"
        elif gesture == "THREE_FINGERS":
            final_status = "SCROLL_MODE"
        elif gesture == "FIST":
            final_status = "PAUSE"
        elif gesture == "FIVE_FINGERS":
            final_status = "VIRTUAL_KEYBOARD"

        # Only process cursor movement if gesture is INDEX_POINT
        if gesture == "INDEX_POINT":
            smoothed_pos = stabilizer.process(hand_data)
        else:
            smoothed_pos = None

        mouse.handle(final_status, smoothed_pos, frame.shape)
    
    display_text = f"Eye: {eye_status} | Hand: {gesture}"
    cv2.putText(frame, display_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    cv2.imshow("TrueEyeballproject", frame)

    key = cv2.waitKey(1)
    if key == ord('q') or key == 27:
        break

auth_manager.lock_session("App exited")
if hasattr(eye_tracker, 'face_mesh'):
    eye_tracker.face_mesh.close()
if hasattr(hand_tracker, 'detector'):
    hand_tracker.detector.close()
cap.release()
cv2.destroyAllWindows()
