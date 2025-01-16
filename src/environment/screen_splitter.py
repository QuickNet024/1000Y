import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import logging

class ScreenSplitter:
    """游戏画面分割处理类
    
    负责将游戏完整截图按照配置切分为不同的功能区域。
    主要功能：
    1. 根据配置文件中的坐标信息切分画面
    2. 支持调试模式显示切分结果
    3. 支持保存切分后的区域图像
    4. 提供区域坐标查询功能
    """
    
    MODULE_NAME = 'ScreenSplitter'
    
    def __init__(self, basic_config: dict, area_config: dict, logger: logging.Logger):
        """初始化屏幕分割器
        
        Args:
            basic_config: 基础配置字典，包含各个区域的坐标信息
            area_config: 区域配置字典，包含各个区域的配置信息
            logger: 日志实例，用于记录处理过程
        """
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<屏幕分割器初始化开始...>>>>>>>>>>>>>>>>>>")
        self.basic_config = basic_config    
        self.area_config = area_config
        self.base_output_dir = Path(basic_config.get('base_output_dir', 'output'))
        self.screenshots_dir = self.base_output_dir / basic_config.get('screenshots_dir', 'original')
        self.logger.info("=========================屏幕分割器初始化完成=========================    ")
    
    def get_region_coords(self, region_name: str) -> Tuple[int, int, int, int]:
        """获取指定区域的坐标信息
        
        Args:
            region_name: 区域名称，必须与配置文件中的区域名对应
            
        Returns:
            Tuple[int, int, int, int]: 返回区域坐标 (x1, y1, x2, y2)
            
        Raises:
            KeyError: 当找不到指定的区域配置时抛出
        """
        if region_name not in self.area_config:
            self.logger.error(f"找不到区域配置: {region_name}")
            raise KeyError(f"找不到区域配置: {region_name}")
        
        # 获取区域坐标
        coords = self.area_config.get(region_name).get('screen_split').get('coordinates')
        self.logger.debug(f"裁切的区域: {region_name} 范围坐标: {coords}")
        return tuple(coords)  # [x1, y1, x2, y2]
    
    def split_region(self, 
                    image: np.ndarray, 
                    region_name: str) -> Optional[np.ndarray]:
        """分割指定区域的图像
        
        Args:
            image: 原始完整截图
            region_name: 要分割的区域名称
            
        Returns:
            Optional[np.ndarray]: 分割后的区域图像，如果分割失败返回None
            
        Note:
            修改返回值为None而不是原始图像，这样可以在process_image中进行错误处理
        """
        try:
            x1, y1, x2, y2 = self.get_region_coords(region_name)
            # 确保坐标在图像范围内
            h, w = image.shape[:2]
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)
            return image[y1:y2, x1:x2]
        except Exception as e:
            self.logger.error(f"分割区域 {region_name} 时出错: {str(e)}")
            return None
    
    def process_image(self,
                     screen_image: np.ndarray,
                     regions_to_process: List[str],
                     save_split: bool = False,
                     debug_mode: bool = False,
                     timestamp: str = None) -> Dict[str, np.ndarray]:
        """处理并分割图像
        
        Args:
            screen_image: 需要分割的原始图像
            regions_to_process: 需要处理的区域列表
            save_split: 是否保存分割后的图像
            debug_mode: 是否显示调试图像
            timestamp: 时间戳，用于调试图像的文件名
            
        Returns:
            Dict[str, np.ndarray]: 分割后的图像字典，key为区域名称
        """
        if screen_image is None:
            raise ValueError("输入图像不能为空")
        
        result_regions = {}
        original_image = screen_image.copy()  # 保存原始图像的副本
        
        # 处理所有区域
        for region_name in regions_to_process:
            try:
                # 始终使用原始图像进行分割
                region_image = self.split_region(original_image, region_name)
                if region_image is None:
                    self.logger.warning(f"区域 {region_name} 分割失败，跳过该区域")
                    continue
                    
                result_regions[region_name] = region_image
                
                # 保存分割图像
                if save_split and timestamp:
                    try:
                        region_dir = self.screenshots_dir / region_name
                        region_dir.mkdir(parents=True, exist_ok=True)
                        save_path = region_dir / f"{timestamp}.png"
                        cv2.imwrite(str(save_path), region_image)
                        self.logger.debug(f"已保存区域图像: {save_path}")
                    except Exception as e:
                        self.logger.error(f"保存区域图像失败: {e}")
                        
            except Exception as e:
                self.logger.error(f"处理区域 {region_name} 时出错: {str(e)}")
                continue
        
        # 调试模式显示图像
        if debug_mode:
            self._show_debug_images(result_regions)
        return result_regions
    
    def get_available_regions(self) -> List[str]:
        """获取所有可用的区域名称列表
        
        Returns:
            List[str]: 所有配置中定义的区域名称列表
        """
        return [name for name in self.basic_config.keys() 
                if isinstance(self.basic_config[name], dict)]
    
    # 调试模式显示图像
    def _show_debug_images(self, result_regions: Dict[str, np.ndarray]):
         while True:
                # 显示所有分割后的图像
                for region_name, image in result_regions.items():
                    window_name = f"original Split Region : {region_name}"
                    cv2.imshow(window_name, image)
                
                # 检查是否按下 'q' 键
                key = cv2.waitKey(100) & 0xFF  # 增加等待时间到100ms
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    break    
    
    def __del__(self):
        """析构函数：确保清理所有OpenCV窗口"""
        cv2.destroyAllWindows() 