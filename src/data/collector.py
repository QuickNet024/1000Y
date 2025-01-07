import time
from pathlib import Path
import numpy as np
from src.environment.screen_capture import ScreenCapture

class DataCollector:
    """数据采集类"""
    
    def __init__(self, config):
        self.config = config
        self.screen_capture = ScreenCapture(config)
        self.save_dir = Path(config.get("save_dir", "data/raw"))
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
    def collect_gameplay(self, duration):
        """采集游戏数据
        
        Args:
            duration: 采集持续时间(秒)
        """
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < duration:
            # 捕获屏幕
            frame = self.screen_capture.capture()
            
            # 保存图像
            save_path = self.save_dir / f"frame_{frame_count}.jpg"
            np.save(str(save_path), frame)
            
            frame_count += 1
            time.sleep(1/30)  # 30fps 