# -*- coding: utf-8 -*-
"""
数据采集器模块

该模块负责:
1. 游戏画面的采集与分割
2. 图像预处理
3. OCR文字识别
4. 数据处理
5. 状态管理
6. 区域依赖关系处理

主要类:
- DataCollector: 数据采集与处理的主类

作者: QuickNet
日期: 2024-01
"""

import sys
from pathlib import Path
import cv2
import keyboard
import time
import numpy as np
from typing import Dict, Optional, List, Union
import logging

# 获取项目根目录并添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入项目内部模块
from src.utils.config_manager import ConfigManager
from src.utils.logger_manager import LoggerManager
from src.environment.screen_capture import ScreenCapture
from src.environment.screen_splitter import ScreenSplitter
from src.environment.window_manager import WindowManager
from src.environment.text_recognizer import TextRecognizer
from src.environment.image_preprocessor import ImagePreprocessor
from src.environment.data_processor import DataProcessor
from src.environment.state_manager import StateManager
from src.environment.action_executor import ActionExecutor


class DataCollector:
    """
    数据采集与处理的主类
    
    该类负责协调整个数据采集和处理流程,包括:
    1. 屏幕捕获
    2. 区域分割
    3. 图像预处理
    4. OCR识别
    5. 数据处理
    6. 状态管理
    
    属性:
        MODULE_NAME (str): 模块名称
        config_manager (ConfigManager): 配置管理器
        logger (Logger): 日志记录器
        basic_config (dict): 基础配置
        area_config (dict): 区域配置
        
    主要组件:
        window_manager: 窗口管理器
        screen_capture: 屏幕捕获器
        screen_splitter: 屏幕分割器
        image_preprocessor: 图像预处理器
        text_recognizer: 文字识别器
        data_processor: 数据处理器
        state_manager: 状态管理器
    """
    
    MODULE_NAME = 'DataCollector'
    
    def __init__(self, logger: logging.Logger, config_manager: ConfigManager):
        """
        初始化数据采集器
        
        Args:
            logger: 日志记录器
            config_manager: 配置管理器
            
        初始化步骤:
        1. 设置配置和日志
        2. 创建必要的目录
        3. 初始化各个处理模块
        4. 初始化状态变量
        """
        self.config_manager = config_manager
        self.logger_config = config_manager.get_logger_config()
        
        # 初始化日志
        self._init_logger()
        
        # 初始化配置
        self._init_config()
        
        # 初始化目录
        self._init_directories()
        
        # 初始化处理模块
        self._init_processors()
        
        # 初始化状态变量
        self._init_variables()
        
        # 初始化窗口位置
        self.window_manager.move_window(0,0)
        self.logger.info("初始化完成")

    def _init_logger(self):
        """
        初始化日志记录器
        
        创建当前类的专用logger实例,用于记录处理过程中的日志信息
        """
        self.logger = LoggerManager(
            name=self.MODULE_NAME,
            **self.logger_config
        ).get_logger()
    # 初始化配置
    def _init_config(self):
        """
        初始化配置信息
        
        从配置管理器获取:
        - 基础配置: 包含全局参数
        - 区域配置: 包含各个区域的具体配置
        """
        self.basic_config = self.config_manager.basic_config
        self.area_config = self.config_manager.area_config
    # 初始化目录结构    
    def _init_directories(self):
        """
        初始化目录结构
        
        创建必要的目录:
        - base_output_dir: 基础输出目录
        - log_dir: 日志目录
        - screenshots_dir: 截图目录
        - preprocessed_dir: 预处理图像目录
        - state_dir: 状态文件目录
        
        所有目录都会自动创建(如果不存在)
        """
        # 基础输出目录
        self.base_output_dir = Path(self.basic_config.get('base_output_dir'))
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        directories = {
            'log_dir': self.basic_config.get('log_dir'),
            'screenshots_dir': self.basic_config.get('screenshots_dir'),
            'preprocessed_dir': self.basic_config.get('preprocessed_dir'),
            'state_dir': self.basic_config.get('state_dir')
        }
        
        for dir_name, dir_path in directories.items():
            full_path = self.base_output_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            setattr(self, dir_name, full_path)
    # 初始化处理模块    
    def _init_processors(self):
        """
        初始化处理模块
        
        创建各个功能模块的实例:
        - window_manager: 窗口管理
        - screen_capture: 屏幕捕获
        - screen_splitter: 屏幕分割
        - image_preprocessor: 图像预处理
        - text_recognizer: 文字识别
        - data_processor: 数据处理
        - state_manager: 状态管理
        
        每个模块都配置独立的logger实例
        """
        # 创建处理模块实例
        processors = {
            'window_manager': (WindowManager, ['basic_config']),
            'screen_capture': (ScreenCapture, ['basic_config']),
            'screen_splitter': (ScreenSplitter, ['basic_config', 'area_config']),
            'image_preprocessor': (ImagePreprocessor, ['basic_config', 'area_config']),
            'text_recognizer': (TextRecognizer, ['basic_config', 'area_config']),
            'data_processor': (DataProcessor, ['basic_config', 'area_config']),
            'state_manager': (StateManager, ['basic_config', 'area_config']),
            'action_executor': (ActionExecutor, ['basic_config'])
        }
        
        for name, (processor_class, config_args) in processors.items():
            # 为每个处理器创建独立的logger
            processor_logger = LoggerManager(
                name=name,
                **self.logger_config
            ).get_logger()
            
            # 构造配置参数
            config_dict = {
                arg: getattr(self, arg) 
                for arg in config_args
            }
            config_dict['logger'] = processor_logger
            
            # 创建处理器实例
            setattr(self, name, processor_class(**config_dict))
    # 初始化状态变量
    def _init_variables(self):
        """
        初始化状态变量
        
        初始化处理过程中需要的各种状态变量:
        - current_screen: 当前屏幕图像
        - capture_image_path: 捕获图像保存路径
        - current_regions: 当前分割的区域
        - split_image_path: 分割图像保存路径
        - preprocessed_images: 预处理后的图像
        - preprocessed_image_path: 预处理图像保存路径
        - ocr_results: OCR识别结果
        - ocr_image_path: OCR结果图像路径
        - timestamp: 当前时间戳
        """
        self.current_screen = None
        self.capture_image_path = None
        self.current_regions = {}
        self.split_image_path = None
        self.preprocessed_images = {}
        self.preprocessed_image_path = None
        self.ocr_results = {}
        self.ocr_image_path = None
        self.timestamp = None
    # 3. 捕获屏幕画面
    def capture_screen(self, save_capture: bool = False) -> np.ndarray:
        """
        捕获当前屏幕画面
        
        Args:
            save_capture: 是否保存捕获的画面
            
        Returns:
            np.ndarray: 捕获的屏幕图像
            
        Raises:
            Exception: 截图失败时抛出异常
        """
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
    # 4. 分割区域
    def split_regions(self, 
                     regions_list: List[str],
                     save_split: bool = False,
                     debug_mode: bool = False,
                     timestamp: str = None) -> Dict[str, np.ndarray]:
        """
        分割指定区域的图像
        
        Args:
            regions_list: 需要分割的区域列表
            save_split: 是否保存分割结果
            debug_mode: 是否启用调试模式
            timestamp: 时间戳
            
        Returns:
            Dict[str, np.ndarray]: 分割后的区域图像字典
        """
        
        self.current_regions = self.screen_splitter.process_image(
            screen_image=self.current_screen,
            regions_to_process=regions_list,
            save_split=save_split,
            debug_mode=debug_mode,
            timestamp=timestamp
        )
        return self.current_regions
    # 5. 预处理图像
    def preprocess_images(self,
                         regions_to_process: Optional[List[str]] = None,
                         debug_mode: bool = False,
                         save_debug: bool = False,
                         timestamp: str = None) -> Dict[str, np.ndarray]:
        """
        对指定区域的图像进行预处理
        
        预处理步骤可能包括:
        - 灰度化
        - 二值化
        - 降噪
        - 边缘检测等
        
        Args:
            regions_to_process: 需要处理的区域列表,为None时处理所有区域
            debug_mode: 是否启用调试模式
            save_debug: 是否保存调试图像
            timestamp: 时间戳,用于保存文件名
            
        Returns:
            Dict[str, np.ndarray]: 预处理后的图像字典,格式为 {区域名: 图像数组}
        """
        # 预处理图像
        self.preprocessed_images = self.image_preprocessor.process_images(
            self.current_regions,
            regions_to_process=regions_to_process,
            save_debug=save_debug,
            debug_mode=debug_mode,
            timestamp=timestamp
        )
        return self.preprocessed_images
    # 6. 文字识别
    def recognize_text(self,
                      regions_to_process: Optional[List[str]] = None,
                      debug_mode: bool = False,
                      save_debug: bool = False,
                      timestamp: str = None) -> Dict[str, dict]:
        """
        对预处理后的图像进行OCR文字识别
        
        Args:
            regions_to_process: 需要识别的区域列表,为None时处理所有区域
            debug_mode: 是否启用调试模式
            save_debug: 是否保存调试图像
            timestamp: 时间戳,用于保存文件名
            
        Returns:
            Dict[str, dict]: OCR识别结果,格式为 {区域名: {文本信息}}
        """
        self.ocr_results = self.text_recognizer.process_regions(
            regions=self.preprocessed_images,  # 直接传入预处理后的图像
            save_debug=save_debug,
            debug_mode=debug_mode,
            timestamp=timestamp
        )
        return self.ocr_results
    # 7. 数据处理
    def process_data(self) -> dict:
        """
        处理OCR识别结果和图像数据
        
        处理步骤:
        1. 解析OCR文本
        2. 提取关键信息
        3. 格式化数据
        4. 验证数据有效性
        
        Returns:
            dict: 处理后的结构化数据
        """
        processed_data = self.data_processor.process(
            self.ocr_results,
            self.preprocessed_images
        )
        return processed_data
    # 8. 处理区域间的依赖关系
    def handle_region_dependencies(self, region_name: str, processed_data: dict):
        """
        处理区域之间的依赖关系
        
        处理逻辑:
        1. 检查区域是否有依赖配置
        2. 根据控制类型处理依赖
        3. 根据状态启用/禁用相关区域
        
        Args:
            region_name: 当前处理的区域名称
            processed_data: 处理后的数据
            
        依赖控制类型:
        - disable_when_false: 当状态为False时禁用依赖区域
        - 其他控制类型可扩展...
        
        示例:
        如果 target_panel 未识别到,则禁用其依赖的 target_info 区域
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
    # 9. 更新状态
    def update_state(self, processed_data: dict, timestamp: str):
        """
        更新状态管理器中的状态信息
        
        Args:
            processed_data: 处理后的数据
            timestamp: 状态更新的时间戳
            
        状态更新可能包括:
        - 游戏场景状态
        - 角色状态
        - 目标状态
        - 任务状态等
        """
        self.state_manager.update(processed_data, timestamp)
    # 10. 获取当前状态
    def get_current_state(self) -> dict:
        """
        获取当前的状态信息
        
        Returns:
            dict: 当前状态的完整信息,包括:
            - 场景状态
            - 角色状态
            - 目标状态
            - 任务状态等
        """
        return self.state_manager.get_current_state()
    # 1.处理一帧画面
    def process_frame(self, regions_list: List[str]) -> dict:
        """
        处理一帧画面的完整流程
        
        处理步骤:
        1. 筛选启用的区域
        2. 捕获屏幕画面
        3. 分割区域
        4. 图像预处理
        5. OCR文字识别
        6. 数据处理
        7. 处理区域依赖
        8. 更新状态
        9. 过滤返回数据
        
        Args:
            regions_list: 需要处理的区域名称列表
            
        Returns:
            dict: 处理后的数据,格式为 {区域名: 处理结果}
            
        Raises:
            Exception: 处理过程中的错误
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
                
            # 在返回之前过滤数据 state_manager 关闭状态的数据就不返回了。
            filtered_data = {}
            for region_name, data in processed_data.items():
                # 检查该区域的state_manager是否启用
                if self.area_config.get(region_name, {}).get('state_manager', {}).get('Enabled', False):
                    filtered_data[region_name] = data
                    self.logger.debug(f"保留区域 {region_name} 的数据用于状态管理")
                else:
                    self.logger.debug(f"区域 {region_name} 的state_manager未启用,跳过其数据")
            
            self.logger.info("帧处理完成")
            return filtered_data  # 返回过滤后的数据
            
        except Exception as e:
            self.logger.error(f"处理帧时出错: {e}", exc_info=True)
            raise

    # 11. 执行动作  
    def execute_action(self, action_type: str, **params):
        """
        执行单个动作
        
        Args:
            action_type: 动作类型('key'/'mouse_move'/'mouse_click')
            **params: 动作参数
        """
        try:
            # 根据动作类型执行相应操作
            if action_type == 'key':  # 键盘按键操作
                if isinstance(params.get('key'), list):
                    # 如果key参数是列表,说明是组合键,调用组合键执行方法
                    # 例如: ['ctrl', 'c'] 表示 Ctrl+C
                    self.action_executor.press_combination(**params)
                else:
                    # 单个按键操作,直接调用按键执行方法
                    # 例如: 'enter' 表示回车键
                    self.action_executor.press_key(**params)
                    
            elif action_type == 'mouse_move':  # 鼠标移动操作
                # 移动鼠标到指定坐标
                # params需包含: x, y 坐标值
                self.action_executor.move_mouse(**params)
                
            elif action_type == 'mouse_click':  # 鼠标点击操作
                # 在指定位置点击鼠标
                # params可包含: x, y 坐标, button 按键类型, clicks 点击次数
                self.action_executor.click_mouse(**params)
                
            else:
                # 未知的动作类型,记录警告日志
                self.logger.warning(f"未知的动作类型: {action_type}")
                
        except Exception as e:
            # 动作执行出现异常时记录错误日志
            self.logger.error(f"动作执行失败: {e}")

    # 12. 执行动作序列  
    def execute_actions(self, actions: List[Dict]):
        """
        执行动作序列
        
        Args:
            actions: 动作序列列表
        """
        self.action_executor.execute_action_sequence(actions)

    
def main():
    """
    主函数
    
    功能:
    1. 初始化配置和日志
    2. 创建数据采集器
    3. 打印区域配置信息
    4. 进入主循环处理画面
    5. 处理退出和异常
    """
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
    processor = DataCollector(
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
            time.sleep(1)  # 每秒处理一次
            
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
    except Exception as e:
        logger.error(f"发生错误: {e}")

if __name__ == "__main__":
    main()
