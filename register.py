import cv2
import sys
from modules.eye_tracker import EyeTracker
from modules.auth import AuthManager

def main():
    username = input("\n[?] Enter the name you want to register: ").strip()

    if not username:
        print("[-] Name cannot be empty.")
        sys.exit(1)

    print(f"\n[+] Starting enrollment for '{username}'...")
    print("    Please look directly at the camera.")

    cap = cv2.VideoCapture(0)
    eye_tracker = EyeTracker()
    
    # We use the special "ENROLLING" mode and tell it the username
    auth_manager = AuthManager(mode="ENROLLING", target_user_id=username)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        
        # Process for face landmarks
        frame, eye_status, face_landmarks = eye_tracker.process(frame)
            
        auth_state, progress = auth_manager.process_face(face_landmarks)
        
        # Draw instructions
        cv2.putText(frame, f"Registering: {username}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Progress: {progress:0.0%}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

        cv2.imshow("Enrollment Setup", frame)

        if auth_state == "ENROLLMENT_COMPLETE":
            print(f"\n[+] Successfully registered user: '{username}'!")
            break

        if cv2.waitKey(1) in [27, ord('q')]:
            print("\n[-] Enrollment cancelled.")
            break
            
    if hasattr(eye_tracker, 'face_mesh'):
        eye_tracker.face_mesh.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
