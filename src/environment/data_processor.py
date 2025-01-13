import cv2
import numpy as np
from typing import Dict, Any, Optional
import re
from pathlib import Path
import logging

class DataProcessor:
    """数据处理类"""
    MODULE_NAME = 'DataProcessor'
    
    def __init__(self, basic_config: dict, area_config: dict, logger: logging.Logger):
        """初始化数据处理器
        
        Args:
            basic_config: 基础配置字典
            logger: 日志实例
        """
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<数据处理器初始化开始...>>>>>>>>>>>>>>>>>>")
        self.basic_config = basic_config
        self.area_config = area_config
        self.current_region_name = None  # 添加属性来存储当前区域名称
        self.current_region_config = None
 
        # 区域名称到处理方法的映射
        self.region_process_mapping = {
            'title_area': self._process_panel_area, # 面板区域
            'game_area': self._process_game_area, # 游戏区域
            'chat_messages': self._process_chat,  # 聊天消息
        }   
        self.logger.info("=========================数据处理器初始化完成=========================")
    # 处理聊天消息
    def _process_chat(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理聊天消息"""
        return {}
        
    # 处理游戏区域数据
    def _process_game_area(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理游戏区域数据"""
        try:
            if not ocr_result or image is None:
                return {}
            
            self.logger.debug("=== 游戏区域OCR结果 ===")
            self.logger.debug(f"原始OCR结果: {repr(ocr_result)}")
            
            name_groups = []
            
            if isinstance(ocr_result, dict) and 'details' in ocr_result:
                for detail in ocr_result['details']:
                    # 清理文本：去除全角和半角符号，只保留中文字符
                    cleaned_text = re.sub(r'[^\u4e00-\u9fff]|[\u3000-\u303F\uFF00-\uFFEF]', '', detail['text'])
                    
                    if cleaned_text:
                        # 直接使用OCR返回的中心点坐标
                        center_x, center_y = detail['center']
                        name_groups.append({
                            'text': cleaned_text,
                            'center_x': center_x,
                            'center_y': center_y
                        })
            
            self.logger.debug(f"最终结果: {name_groups}")
            return {'name_groups': name_groups}
            
        except Exception as e:
            self.logger.error(f"处理游戏区域数据出错: {str(e)}")
            return {}
         
    #    处理面板区域数据
    def _process_panel_area(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理面板区域数据"""
        try:
            if isinstance(ocr_result, dict) and 'text' in ocr_result:
                full_text = ocr_result['text']
            else:
                return {'date': 0, 'time': 0, 'ms': 0}
            
            pattern = r"(\d+\]:)?(?P<date>\d{4}/\d{1,2}/\d{1,2})\s?(?P<time>\d{1,2}:\d{2}:\d{2})[/\(]?(?P<ms>\d+)ms[\)\}]?"
            match = re.match(pattern, full_text)
            if match:
                date = match.group("date")
                time = match.group("time")
                ms = match.group("ms")
                return {'date': date, 'time': time, 'ms': int(ms)}
        except Exception as e:
            self.logger.error(f"处理面板区域数据出错: {str(e)}")
            
        return {'date': 0, 'time': 0, 'ms': 0}
                    
    def process_region(self, region_name: str, ocr_result: Dict, image: np.ndarray, region_config: Dict) -> Dict[str, Any]:
        """处理单个区域的数据
        
        Args:
            region_name: 区域名称
            ocr_result: OCR识别结果
            image: 图像数据
            region_config: 区域配置
            
        Returns:
            Dict: 处理后的数据
        """
        self.current_region_name = region_name
        self.current_region_config = region_config
        
        try:
            # 首先检查是否有针对区域名称的特定处理方法
            if region_name in self.region_process_mapping:
                process_method = self.region_process_mapping[region_name]
                return_data = process_method(ocr_result, image)
                if return_data['date'] != 0:
                    self.logger.debug(f"区域 {region_name} 处理结果: {return_data}")
                else:   
                    self.logger.warning(f"区域 {region_name} 处理结果: 未获取到有效数据")
                return return_data
            # 如果没有特定的处理方法，返回原始OCR结果
            self.logger.warning(f"区域 {region_name} 无特定处理方法，返回原始结果")
            return ocr_result if isinstance(ocr_result, dict) else {'text': str(ocr_result)} if ocr_result else {}
                
        finally:
            self.current_region_name = None
            self.current_region_config = None 