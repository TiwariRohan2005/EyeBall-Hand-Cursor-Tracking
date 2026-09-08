import pyautogui
import numpy as np

class MouseController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0  # Disable pyautogui's built-in pause for smoother streaming
        self.screen_w, self.screen_h = pyautogui.size()

    def handle(self, intent, smoothed_pos, frame_shape):

        if intent == "PAUSE" or intent == "NONE":
            return

        if smoothed_pos:
            x, y = smoothed_pos
            h, w, _ = frame_shape

            # Map stabilized camera coordinates directly to screen
            screen_x = np.interp(x, (0, w), (0, self.screen_w))
            screen_y = np.interp(y, (0, h), (0, self.screen_h))

            pyautogui.moveTo(screen_x, screen_y)

        if intent == "LEFT_CLICK":
            pyautogui.click()
        elif intent == "RIGHT_CLICK":
            pyautogui.rightClick()
            
        elif intent in ["SCROLL_MODE", "WEB_SCROLL_VERTICALLY", "CODE_SCROLL"]:
            pyautogui.scroll(-400)
            
        elif intent == "VOLUME_UP":
            pyautogui.press("volumeup")
            
        elif intent == "VOLUME_DOWN":
            pyautogui.press("volumedown")
            
        elif intent == "PLAY_PAUSE":
            pyautogui.press("playpause")
            
        elif intent == "NEXT_TRACK":
            pyautogui.press("nexttrack")
            
        elif intent == "GO_BACK":
            pyautogui.press("browserback")
            
        elif intent == "VIRTUAL_KEYBOARD":
            # Placeholder for virtual keyboard UI trigger
            pass
