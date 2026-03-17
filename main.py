import cv2
from modules.eye_tracker import EyeTracker
from modules.mouse_actions import MouseController
from modules.hand_tracker import HandTracker

cap = cv2.VideoCapture(0)

eye_tracker = EyeTracker()
hand_tracker = HandTracker()
mouse = MouseController()

prev_x, prev_y = 0, 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    frame, status = eye_tracker.process(frame)
    frame, hand_pos = hand_tracker.process(frame)

    prev_x, prev_y = mouse.handle(status, hand_pos, frame.shape, prev_x, prev_y)

    cv2.putText(frame, f"Status: {status}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("TrueEyeballproject", frame)

    key = cv2.waitKey(1)
    if key == ord('q') or key == 27:
        break

cap.release()
cv2.destroyAllWindows()
