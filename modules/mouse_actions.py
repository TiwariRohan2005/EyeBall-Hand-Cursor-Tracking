import pyautogui
import numpy as np

class MouseController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        self.screen_w, self.screen_h = pyautogui.size()
        self.smooth = 7

    def handle(self, status, hand_pos, frame_shape, prev_x, prev_y):

        if status == "PAUSE":
            return prev_x, prev_y

        if hand_pos:
            x, y = hand_pos
            h, w, _ = frame_shape

            screen_x = np.interp(x, (0, w), (0, self.screen_w))
            screen_y = np.interp(y, (0, h), (0, self.screen_h))

            curr_x = prev_x + (screen_x - prev_x) / self.smooth
            curr_y = prev_y + (screen_y - prev_y) / self.smooth

            pyautogui.moveTo(curr_x, curr_y)

            prev_x, prev_y = curr_x, curr_y

        if status == "LEFT_CLICK":
            pyautogui.click()

        elif status == "RIGHT_CLICK":
            pyautogui.rightClick()

        return prev_x, prev_y
