import time
from pathlib import Path
import numpy as np
from src.environment.screen_capture import ScreenCapture
from src.environment.input_control import InputListener
import cv2
import logging
from datetime import datetime

class DataCollector:
    """数据采集类"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化屏幕捕获
        self.screen_capture = ScreenCapture(config)
        
        # 设置保存目录
        self.save_screenshots_dir = Path(config["screen_data"]["screenshots_file"])
        self.save_screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化输入监听器
        screen_config = config["screen_data"]
        self.input_listener = InputListener(
            keys_to_monitor=set(screen_config["keys_to_monitor"]),
            mouse_area=eval(screen_config["mouse_area"]),
            keyboard_log=screen_config["actions_keyboard_file"],
            mouse_log=screen_config["actions_mouse_file"],
            show_events=config["logging"]["show_input_events"]
        )
        
    def collect_gameplay(self, duration):
        """采集游戏数据"""
        # 开始输入监听
        if not self.input_listener.start():
            self.logger.error("输入监听器启动失败")
            return
        
        self.logger.info("开始记录输入事件，日志保存在:")
        self.logger.info(f"键盘事件记录文件: {self.config['screen_data']['actions_keyboard_file']}")
        self.logger.info(f"鼠标事件记录文件: {self.config['screen_data']['actions_mouse_file']}")
        
        try:
            start_time = time.time()
            frame_count = 0
            fps = self.config["screen_data"]["fps"]

            self.logger.info(f"当前执行FPS值为: {fps}")
            # 根据配置决定是否显示进度
            show_progress = self.config["logging"]["show_progress"]
            
            while time.time() - start_time < duration:
                # 捕获屏幕
                frame = self.screen_capture.capture()
                
                # 保存图像
                # 生成带时间戳的文件名,精确到毫秒
                timestamp = time.time()  # 例如 1697049600.123456
                timestamp_str = f"{timestamp:.6f}".replace(".", "_")  # 例如 "1697049600_123456"
                save_path = self.save_screenshots_dir / f"frame_{frame_count}_{timestamp_str}.png"
                
                # 保存图像并记录日志
                cv2.imwrite(str(save_path), frame)
                self.logger.debug(f"保存图像: {save_path}")
                
                # 显示图像
                cv2.imshow("Captured Image", frame)
                
                # 检查是否按下 'q' 键退出
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.logger.info("用户按下 'q' 键，程序退出")
                    break
                
                frame_count += 1
                
                # 使用精确的时间控制
                next_frame_time = start_time + frame_count * (1.0/fps)
                sleep_time = next_frame_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # 根据配置决定是否显示进度
                if show_progress and frame_count % fps == 0:
                    elapsed_time = time.time() - start_time
                    self.logger.info(f"已采集 {frame_count} 帧，已运行 {elapsed_time:.1f} 秒")
                
        except KeyboardInterrupt:
            self.logger.warning("\n程序被用户中断")
        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}", exc_info=True)
        finally:
            # 停止监听器
            if self.input_listener.stop():
                self.logger.info("输入监听器已停止")
            cv2.destroyAllWindows()
            self.logger.info("\n数据采集完成")
            self.logger.info(f"图像保存在: {self.save_screenshots_dir}")
            self.logger.info(f"输入事件保存在: {Path(self.config['screen_data']['actions_keyboard_file']).parent}")

    def save_frame(self, frame):
        """保存单帧图像"""
        save_path = self.save_screenshots_dir / f"frame_{int(time.time() * 1000)}.jpg"
        cv2.imwrite(str(save_path), frame)
        self.logger.debug(f"保存图像: {save_path}")