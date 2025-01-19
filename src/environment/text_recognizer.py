import logging
import warnings
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict
from paddleocr import PaddleOCR
import os
import sys

class TextRecognizer:
    """文字识别处理类"""
    MODULE_NAME = 'TextRecognizer'
    
    def __init__(self, basic_config: dict, area_config: dict, logger: logging.Logger):
        """初始化文字识别器
        
        Args:
            basic_config: 基础配置字典
            logger: 日志实例
        """
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<文字识别器初始化开始...>>>>>>>>>>>>>>>>>>")
        self.basic_config = basic_config
        self.area_config = area_config
        self.base_output_dir = Path(basic_config.get('base_output_dir', 'output'))
        self.preprocessed_dir = self.base_output_dir / basic_config.get('preprocessed_dir', 'preprocessed')
        self.debug_image_dir = self.preprocessed_dir / "ocr_debug"
        self.debug_image_dir.mkdir(parents=True, exist_ok=True)
        # 从配置中获取OCR参数
        self.show_ocr_log = self.basic_config.get('show_ocr_log', False)
        
        # 根据show_ocr_log设置是否禁用PaddleOCR日志
        if not self.show_ocr_log:
            # 设置环境变量禁用Paddle日志（在导入PaddleOCR之前设置）
            os.environ['PADDLEOCR_LOG'] = '0'
            os.environ['PADDLE_DISABLE_LOG'] = '1'
            os.environ['FLAGS_call_stack_level'] = '0'  # 禁用调用栈日志
            os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit'
            os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.1'
            os.environ['FLAGS_gpu_fraction_of_memory_to_use'] = '0.1'
            os.environ['FLAGS_eager_delete_tensor_gb'] = '0.0'
            os.environ['FLAGS_fast_eager_deletion_mode'] = '1'
            os.environ['FLAGS_use_system_allocator'] = 'true'
            os.environ["KMP_WARNINGS"] = "off"
            os.environ["PYTHONWARNINGS"] = "ignore"
            
            # 禁用所有相关日志
            logging.getLogger().setLevel(logging.ERROR)
            
            # 特别处理 ppocr 的警告日志
            paddle_loggers = [
                "ppocr",
                "paddle", 
                "PIL",
                "paddle.fluid",
                "paddle.distributed.fleet.launch",
                "paddle.distributed.fleet.base.fleet_base",
                "paddle.distributed.fleet.base.distributed_strategy",
                "paddle.distributed.fleet.runtime.runtime_base",
                "paddle.distributed.fleet.runtime.collective_runtime",
                "paddle.distributed.fleet.runtime.parameter_server_runtime"
            ]
            
            for logger_name in paddle_loggers:
                paddle_logger = logging.getLogger(logger_name)
                paddle_logger.setLevel(logging.ERROR)
                paddle_logger.propagate = False
                paddle_logger.disabled = True  # 完全禁用日志器
                # 移除所有已存在的处理器
                for handler in paddle_logger.handlers[:]:
                    paddle_logger.removeHandler(handler)
            
            # 禁用所有警告
            warnings.filterwarnings('ignore')
            warnings.simplefilter("ignore")
            
            # 重定向标准错误输出
            sys.stderr = open(os.devnull, 'w')
        
        # 初始化默认OCR实例
        self.ocr = self._create_ocr_instance()
        
    def _create_ocr_instance(self, custom_params: dict = None) -> PaddleOCR:
        """创建OCR实例
        
        Args:
            custom_params: 自定义OCR参数，如果提供则会覆盖默认参数
            
        Returns:
            PaddleOCR: 配置好的OCR实例
        """
        try:
            # 默认OCR配置
            default_config = {
                'use_gpu': True,
                'lang': 'ch',
                'show_log': self.show_ocr_log,
                'use_angle_cls': False,
                'det': True,
                'rec': True,
                'det_algorithm': 'DB',
                'det_limit_side_len': 1040,
                'det_limit_type': 'max',
                'det_db_thresh': 0.2,
                'det_db_box_thresh': 0.3,
                'det_db_unclip_ratio': 1.6,
                'rec_algorithm': 'SVTR_LCNet',
                'rec_batch_num': 1,
                'cls_batch_num': 1,
                'enable_mkldnn': True,
                'cpu_threads': 4,
                'rec_char_type': 'ch', 
                'rec_model_dir': "F:/2025Projects/1000Y/models/ch_PP-OCRv4_det",
                'drop_score': 0.5,
                'use_space_char': True,
                'det_box_thresh': 0.2,
                'det_unclip_ratio': 1.0,
                'use_dilation': False,
                'det_db_score_mode': 'fast',
                # 新增参数，优化文本行检测
                #'det_db_use_dilation': True,    # 使用膨胀，有助于连接断开的文本
                'det_east_score_thresh': 0.8,   # EAST文本检测分数阈值
                'det_east_cover_thresh': 0.1,   # EAST文本检测覆盖阈值
                'det_east_nms_thresh': 0.2,     # EAST非极大值抑制阈值
                # 新增识别参数
                # 'rec_image_shape': "3, 48, 320", # 调整识别图片大小，适合小文字
                # 'max_text_length': 25,           # 最大文本长度
                'rec_char_dict_path': None,      # 使用默认字典

            }
            
            # 如果有自定义参数，更新配置
            if custom_params:
                default_config.update(custom_params)
                self.logger.debug(f"使用自定义OCR参数: {custom_params}")
            
            # 创建并返回OCR实例
            return PaddleOCR(**default_config)
            
        except Exception as e:
            self.logger.error(f"创建OCR实例失败: {e}")
            raise
            
    # 处理图像并识别文字
    def process_and_recognize(self, 
                            image: np.ndarray,
                            save_debug: bool = False,
                            debug_mode: bool = False,
                            debug_path: Optional[Path] = None,
                            timestamp: str = None,
                            region_name: str = None) -> Dict:
        """处理图像并识别文字
        
        Returns:
            Dict: 包含处理后的OCR结果，格式为：
            {
                'details': [
                    {
                        'text': '识别的文本',
                        'confidence': 置信度,
                        'box': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
                        'center': [center_x, center_y]  # 添加中心点坐标
                    },
                    ...
                ]
            }
        """
        try:
            # 根据区域配置创建OCR实例
            current_ocr = self.ocr  # 默认使用基础OCR实例
            
            if region_name and region_name in self.area_config:
                region_config = self.area_config[region_name]
                ocr_params = region_config.get('text_recognizer', {}).get('ocr_params', {})
                
                if ocr_params:
                    try:
                        current_ocr = self._create_ocr_instance(ocr_params)
                    except Exception as e:
                        self.logger.error(f"创建区域特定OCR实例失败: {e}, 使用默认OCR实例")
                        current_ocr = self.ocr

            # 保存调试图像
            if save_debug and debug_mode and debug_path and timestamp:
                debug_dir = Path(debug_path)
                debug_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(debug_dir / f'{timestamp}.png'), image)
            
            # 执行OCR识别
            result = current_ocr.ocr(image, cls=False)
            
            if not result or not result[0]:
                return {'details': []}
            
            # 转换结果格式
            formatted_results = []
            for line in result[0]:  # result[0]包含所有识别结果
                if len(line) == 2:  # 确保结果包含坐标和文本信息
                    box, (text, confidence) = line
                    
                    # 计算中心点坐标
                    center_x = sum(point[0] for point in box) / 4
                    center_y = sum(point[1] for point in box) / 4
                    
                    # 格式化单个结果
                    formatted_result = {
                        'text': text,
                        'confidence': float(confidence),
                        'box': [[int(x), int(y)] for x, y in box],
                        'center': [int(center_x), int(center_y)]
                    }
                    formatted_results.append(formatted_result)
            
            return {'details': formatted_results}
            
        except Exception as e:
            self.logger.error(f"文字识别出错: {str(e)}")
            return {'details': []}
    
    # 处理多个区域的图像并识别文字
    def process_regions(self, 
                       regions: Dict[str, np.ndarray],
                       save_debug: bool = False,
                       debug_mode: bool = False,
                       timestamp: str = None) -> Dict[str, str]:
        """处理多个区域的图像并识别文字"""
        results = {}
        
        for region_name, region_image in regions.items():
            self.logger.debug(f"处理区域: {region_name}")
            
            # 设置调试路径
            if save_debug and self.debug_image_dir:
                region_debug_path = self.debug_image_dir / region_name
                region_debug_path.mkdir(parents=True, exist_ok=True)
            else:
                region_debug_path = None
            
            # 处理并识别，传入区域名称
            text = self.process_and_recognize(
                image=region_image,
                save_debug=save_debug,
                debug_mode=debug_mode,
                debug_path=region_debug_path,
                timestamp=timestamp,
                region_name=region_name  # 添加区域名称参数
            )
            
            results[region_name] = text
            self.logger.debug(f"区域 {region_name} 识别结果: {text}")
            
        return results 