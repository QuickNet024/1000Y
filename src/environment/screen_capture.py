import mss
import cv2
import numpy as np

class ScreenCapture:
    """屏幕捕获类"""
    
    def __init__(self, config):
        self.config = config
        self.sct = mss.mss()
        
    def capture(self):
        """捕获屏幕画面"""
        monitor = self.config.get("monitor", {"top": 0, "left": 0, "width": 1920, "height": 1080})
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) 