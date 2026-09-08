import cv2
import numpy as np
from modules.ui.keyboard_manager import VirtualKeyboardManager
from modules.ui.interaction_engine import InteractionEngine

def main():
    print("Starting Virtual Keyboard Test UI...")
    print("Move your mouse over the window to test hover states!")
    print("Left click to test selection state.")
    print("Press 'D' to toggle disabled (Auth lock) state.")
    print("Press 'S' to test prediction suggestion state.")
    print("Press 'Q' or ESC to exit.")
    
    # Create the manager and intelligence engine
    kb_manager = VirtualKeyboardManager()
    interaction_engine = InteractionEngine()
    
    cv2.namedWindow("Keyboard Test UI")
    
    # Track fake mouse state for testing hooks
    mouse_x, mouse_y = 0, 0
    clicked = False
    
    def on_mouse(event, x, y, flags, param):
        nonlocal mouse_x, mouse_y, clicked
        mouse_x, mouse_y = x, y
        if event == cv2.EVENT_LBUTTONDOWN:
            clicked = True

    cv2.setMouseCallback("Keyboard Test UI", on_mouse)

    locked = False
    suggest = False
    
    while True:
        # Create a mock 720p backdrop
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Add a subtle gradient or color to see the glassmorphism alphablend effectively
        frame[:] = (40, 30, 30)
        
        cv2.putText(frame, "TrueEyeball - Keyboard UI Sandbox", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        
        # 1. Feed mock prediction engine state
        if suggest and not locked:
            kb_manager.highlight_predictions(["T", "H", "E", "Enter", "Space"])
            
        # 2. Feed intelligence engine
        active_key, confidence, ready_for_blink = None, 0.0, False
        if not locked and not suggest:
            active_key, confidence, ready_for_blink = interaction_engine.process(mouse_x, mouse_y, kb_manager)
            
        # 3. Simulate eye tracker confirmation (Only works if engine says ready!)
        if clicked and not locked:
            clicked = False
            if ready_for_blink and active_key:
                print(f"Blink Confirmed: {active_key.label} (Confidence: 100%)")
                active_key.update_state("selected")
            else:
                print("Click ignored: Hover confidence not reached or jitter detected.")
            
        # 4. Render!
        frame = kb_manager.render(frame)
        
        cv2.imshow("Keyboard Test UI", frame)
        
        key = cv2.waitKey(1)
        if key in [27, ord('q')]:
            break
        elif key == ord('d'):
            locked = not locked
            kb_manager.set_global_state(locked)
            print(f"Global Lock (Auth State): {locked}")
        elif key == ord('s'):
            suggest = not suggest
            print(f"Prediction Highlights: {suggest}")
            if not suggest and not locked:
                for k in kb_manager.keys:
                    k.update_state("idle")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
