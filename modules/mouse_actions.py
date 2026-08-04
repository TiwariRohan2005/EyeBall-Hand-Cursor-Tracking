import pyautogui
import numpy as np

class MouseController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0  # Disable pyautogui's built-in pause for smoother streaming
        self.screen_w, self.screen_h = pyautogui.size()

    def handle(self, status, smoothed_pos, frame_shape):

        if status == "PAUSE":
            return

        if smoothed_pos:
            x, y = smoothed_pos
            h, w, _ = frame_shape

            # Map stabilized camera coordinates directly to screen
            screen_x = np.interp(x, (0, w), (0, self.screen_w))
            screen_y = np.interp(y, (0, h), (0, self.screen_h))

            pyautogui.moveTo(screen_x, screen_y)

        if status == "LEFT_CLICK":
            pyautogui.click()

        elif status == "RIGHT_CLICK":
            pyautogui.rightClick()
            
        elif status == "SCROLL_MODE":
            # For now, let's just trigger a small static scroll down as a proof of concept
            pyautogui.scroll(-200)
            
        elif status == "VIRTUAL_KEYBOARD":
            # Placeholder for virtual keyboard
            pass
