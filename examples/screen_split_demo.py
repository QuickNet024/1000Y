# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import cv2
import keyboard
import yaml
import time
import numpy as np
from typing import Dict, Optional, List, Union
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.environment.screen_capture import ScreenCapture
from src.environment.screen_splitter import ScreenSplitter
from src.environment.window_manager import WindowManager
from src.environment.text_recognizer import TextRecognizer
from src.environment.image_preprocessor import ImagePreprocessor
from src.environment.data_processor import DataProcessor
from src.environment.state_manager import StateManager
from src.utils.config_manager import ConfigManager
from src.utils.logger_manager import LoggerManager

class GameScreenProcessor:
    """游戏画面处理主类"""
    MODULE_NAME = 'GameScreenProcessor'
    
    def __init__(self, logger: logging.Logger, config_manager: ConfigManager):
        """初始化游戏画面处理器"""
        self.config_manager = config_manager
        self.logger_config = config_manager.get_logger_config()
        
        # 为自己创建logger
        self.logger = LoggerManager(
            name=self.MODULE_NAME,
            **self.logger_config
        ).get_logger()
        
        # 获取基础配置
        self.basic_config = self.config_manager.basic_config
        self.area_config = self.config_manager.area_config
        # 初始化基础输出目录    
        self.base_output_dir = Path(self.basic_config.get('base_output_dir'))
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        # 初始化日志目录
        self.log_dir = Path(self.base_output_dir/self.basic_config.get('log_dir'))
        self.log_dir.mkdir(parents=True, exist_ok=True)   
        # 初始化原始截图目录
        self.screenshots_dir = Path(self.base_output_dir/self.basic_config.get('screenshots_dir'))
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        # 初始化预处理截图目录
        self.preprocessed_dir = Path(self.base_output_dir/self.basic_config.get('preprocessed_dir'))
        self.preprocessed_dir.mkdir(parents=True, exist_ok=True)
        # 初始化状态目录
        self.state_dir = Path(self.base_output_dir/self.basic_config.get('state_dir'))
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # 初始化各个模块，为每个模块创建独立的logger
        self.window_manager = WindowManager(
            basic_config=self.basic_config,
            logger=LoggerManager(name='WindowManager', **self.logger_config).get_logger()
        )
        
        self.screen_capture = ScreenCapture(
            basic_config=self.basic_config,
            logger=LoggerManager(name='ScreenCapture', **self.logger_config).get_logger()
        )
        
        self.screen_splitter = ScreenSplitter(
            basic_config=self.basic_config,
            area_config=self.area_config,   
            logger=LoggerManager(name='ScreenSplitter', **self.logger_config).get_logger()
        )
        
        self.image_preprocessor = ImagePreprocessor(
            basic_config=self.basic_config,
            area_config=self.area_config,
            logger=LoggerManager(name='ImagePreprocessor', **self.logger_config).get_logger()
        )
        
        self.text_recognizer = TextRecognizer(
            basic_config=self.basic_config,
            area_config=self.area_config,
            logger=LoggerManager(name='TextRecognizer', **self.logger_config).get_logger()
        )
        
        self.data_processor = DataProcessor(
            basic_config=self.basic_config,
            area_config=self.area_config,
            logger=LoggerManager(name='DataProcessor', **self.logger_config).get_logger()
        )
        
        self.state_manager = StateManager(
            basic_config=self.basic_config,
            area_config=self.area_config,
            logger=LoggerManager(name='StateManager', **self.logger_config).get_logger()
        )
        
        # 初始化变量
        self.current_screen = None      #
        self.capture_image_path = None  # 捕获的原始图像
        self.current_regions = {}       # 分割后的图像
        self.split_image_path = None    # 分割后的图像路径      
        self.preprocessed_images = {}   # 预处理后的图像
        self.preprocessed_image_path = None # 预处理后的图像路径
        self.ocr_results = {}           # OCR识别结果   
        self.ocr_image_path = None      # OCR识别后的图像路径
        self.timestamp = None           # 时间戳
        self.window_manager.move_window(0,0)  # 移动窗口到屏幕左上角
        self.logger.info("初始化完成")
        
    def capture_screen(self,save_capture: bool = False) -> np.ndarray:
        """捕获屏幕"""
        try:
            # 捕获屏幕
            self.current_screen = self.screen_capture.capture()
            # 如果开启了截屏保存图片原始模式，保存截图
            if save_capture:
                # 保存截图
                filename = f"original_{self.timestamp}.png"
                save_path = self.screenshots_dir / filename
                cv2.imwrite(str(save_path), self.current_screen)
                self.capture_image_path = save_path
                self.logger.debug(f"已保存原始截图: {save_path}") 
                 
            return self.current_screen 
            
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            raise
    # 分割区域
    def split_regions(self, 
                     regions_list: List[str],
                     save_split: bool = False,
                     debug_mode: bool = False,
                     timestamp: str = None) -> Dict[str, np.ndarray]:
        """分割指定区域"""
        
        self.current_regions = self.screen_splitter.process_image(
            screen_image=self.current_screen,
            regions_to_process=regions_list,
            save_split=save_split,
            debug_mode=debug_mode,
            timestamp=timestamp
        )
        return self.current_regions
    # 预处理图像
    def preprocess_images(self,
                         regions_to_process: Optional[List[str]] = None,
                         debug_mode: bool = False,
                         save_debug: bool = False,
                         timestamp: str = None) -> Dict[str, np.ndarray]:
        """预处理图像"""
        # 预处理图像
        self.preprocessed_images = self.image_preprocessor.process_images(
            self.current_regions,
            regions_to_process=regions_to_process,
            save_debug=save_debug,
            debug_mode=debug_mode,
            timestamp=timestamp
        )
        return self.preprocessed_images
    # 文字识别
    def recognize_text(self,
                      regions_to_process: Optional[List[str]] = None,
                      debug_mode: bool = False,
                      save_debug: bool = False,
                      timestamp: str = None) -> Dict[str, dict]:
        """文字识别"""
        if regions_to_process is None:
            regions_to_process = list(self.preprocessed_images.keys())
        
        # 只传入需要处理的区域的图像
        regions_to_ocr = {
            name: self.preprocessed_images[name]
            for name in regions_to_process
            if name in self.preprocessed_images
        }
        
        self.ocr_results = self.text_recognizer.process_regions(
            regions=regions_to_ocr,
            save_debug=save_debug,
            debug_mode=debug_mode,
            timestamp=timestamp
        )
        return self.ocr_results
    # 数据处理
    def process_data(self) -> dict:
        """数据处理"""
        processed_data = self.data_processor.process(
            self.ocr_results,
            self.preprocessed_images
        )
        return processed_data
    # 更新状态
    def update_state(self, processed_data: dict, timestamp: str):
        """更新状态"""
        self.state_manager.update(processed_data, timestamp)
    # 获取当前状态
    def get_current_state(self) -> dict:
        """获取当前状态"""
        return self.state_manager.get_current_state()
    # 处理一帧画面
    def process_frame(self, regions_list: List[str]) -> dict:
        """处理一帧画面的完整流程
        
        Args:
            regions_list: 需要处理的区域名称列表，与配置文件中的区域名对应
            
        Returns:
            dict: 处理后的数据，格式为 {区域名: 处理结果}
        """
        # 生成时间戳，用于调试图片的保存等
        # 确保时间戳小数点后有7位数字
        timestamp = f"{time.time():.7f}".replace('.', '_')
            
        self.timestamp = timestamp
        # 初始化处理结果字典
        processed_data = {}
        
        try:
            # 1. 从配置中筛选出已启用的区域
            enabled_regions = [
                region_name for region_name in regions_list
                if self.area_config.get(region_name, {}).get('Enabled', False)
            ]
            
            self.logger.info(f"开始处理区域: {enabled_regions}")
            
            # 2. 逐个处理每个启用的区域
            for region_name in enabled_regions:
                # 获取当前区域的配置信息
                region_config = self.area_config.get(region_name)
                if not region_config:
                    self.logger.warning(f"找不到区域配置: {region_name}")
                    continue
                    
                # 获取调试相关配置
                debug_mode = region_config.get('debug_mode').get('Enabled')
                save_debug = region_config.get('save_debug').get('Enabled')
                
                self.logger.debug(f"处理区域 {region_name} - debug_mode: {debug_mode}, save_debug: {save_debug}")
                    
                # 3. 屏幕捕获 (只在处理第一个区域时执行一次)
                if region_name == enabled_regions[0]:
                    if region_config.get('screen_capture').get('Enabled',True):
                        self.logger.info(f"捕获屏幕区域: {region_name}")
                        save_capture = region_config.get('screen_capture').get('save_capture')
                        self.capture_screen(save_capture = save_capture)
                
                # 4. 区域分割
                # 根据配置的坐标将完整屏幕图像分割成各个区域
                if region_config.get('screen_split').get('Enabled'):
                    self.logger.info(f"分割区域: {region_name}")
                    save_split = region_config.get('screen_split').get('save_split')
                    self.split_regions([region_name], 
                                     save_split=save_split,
                                     debug_mode=debug_mode,
                                     timestamp=timestamp,
                                     )
                
                # 5. 图像预处理
                # 对分割后的区域图像进行预处理（如二值化、降噪等）
                if region_config.get('image_preprocess', {}).get('Enabled'):
                    self.logger.info(f"预处理图像: {region_name}")
                    self.preprocess_images([region_name], 
                                        save_debug=save_debug,
                                        debug_mode=debug_mode,
                                        timestamp=timestamp)
                else:
                    # 当预处理被禁用时，直接使用分割后的原始图像
                    self.preprocessed_images = self.current_regions
                
                # 6. OCR文字识别
                # 对预处理后的图像进行OCR识别
                if region_config.get('text_recognizer', {}).get('Enabled'):
                    self.logger.info(f"文字识别: {region_name}")
                    ocr_results = self.recognize_text([region_name],
                                                        debug_mode=debug_mode,
                                                        save_debug=save_debug,  
                                                   timestamp=timestamp)
                    # 如果有识别结果，保存到处理结果字典中
                    if ocr_results:
                        processed_data[region_name] = ocr_results.get(region_name, {})
                else:   
                    # 如果OCR被禁用，则直接使用预处理后的图像
                    processed_data[region_name] = self.preprocessed_images.get(region_name, {})

                # 7. 数据处理       
                # 对OCR结果进行后处理（如数据提取、格式化等）
                if region_config.get('data_processor', {}).get('Enabled'):
                    self.logger.info(f"数据处理: {region_name}")
                    if region_name in processed_data:  
                        processed_data[region_name] = self.data_processor.process_region(
                            region_name,
                            processed_data[region_name],  # OCR结果
                            self.preprocessed_images.get(region_name),  # 预处理后的图像
                            region_config  # 区域配置
                        )
                        
                # 8. 处理区域依赖关系
                self.handle_region_dependencies(region_name, processed_data)

                
            # 9. 状态更新
            # 在所有区域处理完成后，更新整体状态 
            if any(self.area_config[r].get('state_manager', {}).get('Enabled') 
                    for r in regions_list):
                self.update_state(processed_data, timestamp)
                
            self.logger.info("帧处理完成")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"处理帧时出错: {e}", exc_info=True)
            raise

    # 处理区域间的依赖关系
    def handle_region_dependencies(self, region_name: str, processed_data: dict):
        """处理区域间的依赖关系
        
        Args:
            region_name: 当前处理的区域名称
            processed_data: 处理后的数据
        """
        # 检查区域是否有依赖配置
        if not self.area_config[region_name].get('dependencies'):
            return
        
        dependencies = self.area_config[region_name].get('dependencies', [])
        control_type = self.area_config[region_name].get('control_type')
        
        # 根据不同的控制类型处理依赖
        if control_type == "disable_when_false":
            status_key = f"status"  # 例如: target_panel_status
            if processed_data[region_name].get(status_key) == False:
                # 关闭相关检测
                for dep in dependencies:
                    if dep in self.area_config:
                        self.area_config[dep]['Enabled'] = False
                self.logger.info(f"{region_name}未识别到,已关闭相关检测: {dependencies}")
            else:
                # 重新开启相关检测
                for dep in dependencies:
                    if dep in self.area_config:
                        self.area_config[dep]['Enabled'] = True
                self.logger.info(f"{region_name}已识别到,重新开启相关检测: {dependencies}")

def main():
    """主函数"""
    # 配置文件路径
    basic_config_path = project_root / "config/env/status_collection_config.yaml"

    # 使用配置管理器获取日志配置
    config_manager = ConfigManager(basic_config_path)
    logger_config = config_manager.get_logger_config()
    
    # 初始化主程序日志（只初始化一次）
    logger = LoggerManager(
        name='Main',
        **logger_config
    ).get_logger()


    
    # 创建处理器
    processor = GameScreenProcessor(
        config_manager=config_manager,      # 传递配置管理器
        logger=logger                       # 直接传递logger实例       
    )
    

    # 打印处理区域信息
    logger.debug("开始打印准备处理的所有区域配置信息:")
    for region_name, config in config_manager.config.items():
        # 跳过基础配置
        if region_name == 'basic_config':
            continue
        # 只处理字典类型的配置（区域配置）
        if isinstance(config, dict):
            logger.debug(f"区域: {region_name} ({config.get('name_zh', '')})")
            logger.debug(f"├── 区域启用状态: {config.get('Enabled')}")
            logger.debug(f"├── 截图模块: {config.get('screen_capture', {}).get('Enabled')}")
            logger.debug(f"├── 分割模块: {config.get('screen_split', {}).get('Enabled')}")
            logger.debug(f"├── 预处理模块: {config.get('image_preprocess', {}).get('Enabled')}")
            logger.debug(f"├── OCR模块: {config.get('text_recognizer', {}).get('Enabled')}")
            logger.debug(f"├── 数据处理模块: {config.get('data_processor', {}).get('Enabled')}")
            logger.debug(f"├── 状态管理模块: {config.get('state_manager', {}).get('Enabled')}")
            logger.debug(f"├── 调试模式: {config.get('debug_mode', {}).get('Enabled')}")
            logger.debug(f"└── 保存调试图像: {config.get('save_debug', {}).get('Enabled')}")

    # 获取所有需要处理的区域（排除基础配置）
    regions_to_process = [
        name for name in config_manager.config.keys()
        if name != 'basic_config' and isinstance(config_manager.config[name], dict)
    ]
    
    try:
        while True:
            # 记录循环开始时间
            loop_start_time = time.time()
            
            # 处理一帧画面
            processed_data = processor.process_frame(regions_to_process)
            logger.info(f"处理结果: {processed_data}")
            
            # 检查是否按下 'q' 键退出
            if keyboard.is_pressed('q'):
                logger.info("程序退出")
                break
                
            # 计算循环耗时
            loop_time = time.time() - loop_start_time
            logger.info(f"本次循环耗时: {loop_time:.3f}秒")
            
            # 控制处理频率
            time.sleep(3)  # 每秒处理一次
            
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
    except Exception as e:
        logger.error(f"发生错误: {e}")

if __name__ == "__main__":
    main()
