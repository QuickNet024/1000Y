import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging


class ImagePreprocessor:
    """图像预处理类"""
    MODULE_NAME = 'ImagePreprocessor'
    
    def __init__(self, basic_config: dict, area_config: dict, logger: logging.Logger):
        """初始化图像预处理器
        
        Args:
            basic_config: 基础配置字典
            logger: 日志实例
        """
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<图像预处理器初始化开始...>>>>>>>>>>>>>>>>>>")
        self.basic_config = basic_config
        self.area_config = area_config
        self.base_output_dir = Path(basic_config.get('base_output_dir', 'output'))
        self.preprocessed_dir = self.base_output_dir / basic_config.get('preprocessed_dir', 'preprocessed')   
        # 针对具体区域名称的预处理方法映射
        self.region_specific_methods = {
            'title_area': self._preprocess_title_area,  # 标题区域
            'game_area': self._preprocess_game_area,  # 游戏区域 
            'chat_messages': self._preprocess_chat_messages,  # 聊天消息区域
            # 可以继续添加更多区域特定的处理方法...
        }
        self.logger.info("=========================图像预处理器初始化完成=========================    ")
    
    # 聊天消息区域预处理
    def _preprocess_chat_messages(self, image: np.ndarray) -> np.ndarray:
        """聊天消息区域预处理"""
        return image
    
    # 游戏区域预处理
    def _preprocess_game_area(self, image: np.ndarray) -> np.ndarray:
        """
        为图像添加遮罩并显示结果。

        参数:
            mask_height (int): 遮罩的高度（默认 20 像素）。
            spacing (int): 遮罩之间的间隔（默认 16 像素）。
        """
        # 遮罩参数
        mask_height=20
        spacing=16

        # 获取图像的高度和宽度
        height, width = image.shape[:2]

        # 创建一个纯黑色的遮罩
        mask = np.zeros((mask_height, width, 3), dtype=np.uint8)  # 3 通道（BGR）

        # 在图像上添加第一个遮罩（水平条纹）
        y = 0
        while y < height:
            # 添加遮罩
            if y + mask_height <= height:
                image[y:y + mask_height, 0:width] = mask
            else:
                # 如果剩余高度不足，只填充剩余部分
                image[y:height, 0:width] = mask[:height - y, :]         
            # 更新 y 坐标，跳过间隔
            y += mask_height + spacing

        # 定义多个遮罩区域的坐标
        mask_regions = [
            (0, 10, 960, 122),  # 第一个矩形区域
            (0, 0, width, 127),   # 第二个矩形区域
            (10, 322, 191, 364),   # 第三个矩形区域
            (20, 139, 116, 200),    # 第四个矩形区域
        ]
        
        # 添加多个遮罩区域
        for region in mask_regions:
            x1, y1, x2, y2 = region
            image[y1:y2, x1:x2] = 0  # 将指定区域填充为纯黑色
        # 反转图像
        image = cv2.bitwise_not(image)
        # -------------------------------------------------------------------------------------------
        # 将图像从 BGR 转换为 HSV 颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 定义红色的范围（HSV 颜色空间）
        lower_red = np.array([0, 50, 50])  # 红色的下限
        upper_red = np.array([10, 255, 255])  # 红色的上限

        # 创建一个掩码，标记红色区域    *蓝色文字也变黑色
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        # 创建一个掩码，标记 R=255 且 B=255 的区域    *绿色文字也变黑色
        rb_mask = (image[:, :, 0] >= 255) & (image[:, :, 2] >= 255) & (image[:, :, 1] < 10)     # 绿色文字也变黑色
        # 将红色区域和 R=255 且 B=255 的区域填充为黑色
        image[red_mask == 255] = [0, 0, 0]      # 红色区域
        image[rb_mask] = [0, 0, 0]              # R=255 且 B=255 的区域

        # 将图像转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 二值化处理（阈值为 15）
        _, binary = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)

        return binary
    # 预处理标题区域
    def _preprocess_title_area(self, image: np.ndarray) -> np.ndarray:
        """标题区域预处理"""
        # 转换为灰度图并进行自适应二值化
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 二值化
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    def show_debug_window(self, region_name: str, image: np.ndarray) -> None:
        """显示调试窗口
        
        Args:
            region_name: 区域名称
            image: 要显示的图像
        """
        window_name = f"Preprocessed-{region_name}"
        cv2.imshow(window_name, image)
        # 非阻塞方式检查按键，如果按下'q'则关闭所有窗口
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()

    def process_images(self,
                      images: Dict[str, np.ndarray],
                      regions_to_process: Optional[List[str]] = None,
                      debug_mode: bool = False,
                      save_debug: bool = False,
                      timestamp: str = None) -> Dict[str, np.ndarray]:
        """处理多个区域的图像"""
        processed_images = {}
        
        if regions_to_process is None:
            regions_to_process = list(images.keys())
        
        for region_name in regions_to_process:
            if region_name not in images:
                continue
                
            # 获取区域配置
            region_config = self.area_config.get(region_name, {})

            # 获取处理方法
            preprocess_method = self.region_specific_methods.get(region_name)
            if not preprocess_method:
                self.logger.debug(f"区域 {region_name} 无特定处理方法，返回原图")
                processed_images[region_name] = images[region_name].copy()
                continue
            
            # 预处理图像
            processed_image = preprocess_method(images[region_name])
            processed_images[region_name] = processed_image

            # 保存调试图像
            if save_debug and timestamp:
                try:
                    region_dir = self.preprocessed_dir / region_name
                    region_dir.mkdir(parents=True, exist_ok=True)
                    save_path = region_dir / f"{timestamp}.png"
                    cv2.imwrite(str(save_path), processed_image)
                    self.logger.debug(f"已保存预处理图像: {save_path}")
                except Exception as e:
                    self.logger.error(f"保存预处理图像失败: {e}")

        # 如果开启了调试模式，显示所有处理后的图像
        if debug_mode:
            while True:
                # 显示所有处理后的图像
                for region_name, image in processed_images.items():
                    cv2.imshow(f"Preprocessed-{region_name}", image)
                
                # 检查是否按下 'q' 键
                if cv2.waitKey(100) & 0xFF == ord('q'):  # 增加等待时间到100ms
                    cv2.destroyAllWindows()
                    break

        return processed_images

    def __del__(self):
        """析构函数：清理所有窗口"""
        cv2.destroyAllWindows() 