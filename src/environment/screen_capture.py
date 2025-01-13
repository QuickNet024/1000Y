import mss
import cv2
import numpy as np
from pathlib import Path
import logging

class ScreenCapture:
    """屏幕捕获类"""
    MODULE_NAME = 'ScreenCapture'
    
    def __init__(self, basic_config: dict, logger: logging.Logger):
        """初始化屏幕捕获器
        
        Args:
            basic_config: 基础配置字典
            area_config: 区域配置字典
            logger: 日志实例
        """
        # 初始化日志
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<屏幕捕获器初始化开始...>>>>>>>>>>>>>>>>>>")
        self.basic_config = basic_config
        # 获取屏幕区域配置
        screen_config = self.basic_config.get('screen_capture', {})
        if not screen_config:
            raise ValueError("未找到屏幕捕获配置")
        # 获取捕获区域
        self.capture_area = {
            'top': screen_config.get('top', 0),
            'left': screen_config.get('left', 0),
            'width': screen_config.get('width', 1920),
            'height': screen_config.get('height', 1080)
        }
        
        self.logger.debug(f"捕获区域设置: {self.capture_area}")
        
        try:
            self.sct = mss.mss()
            self.logger.info("=========================屏幕捕获器初始化完成=========================    ")
        except Exception as e:
            self.logger.error(f"屏幕捕获器初始化失败: {e}")
            raise
        
    def capture(self):
        """捕获屏幕画面"""
        try:
            screenshot = self.sct.grab(self.capture_area)
            img = np.array(screenshot)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            self.logger.error(f"屏幕捕获失败: {e}")
            raise 