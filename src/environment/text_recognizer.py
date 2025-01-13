import logging
import warnings
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict
from paddleocr import PaddleOCR
import os

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
            # 设置环境变量禁用Paddle日志
            os.environ['PADDLEOCR_LOG'] = '0'
            os.environ['PADDLE_DISABLE_LOG'] = '1'
            os.environ["KMP_WARNINGS"] = "off"
            # 禁用所有相关日志
            logging.getLogger().setLevel(logging.ERROR)
            for logger_name in ["ppocr", "paddle", "PIL", "paddle.fluid", "paddle.distributed.fleet.launch"]:
                paddle_logger = logging.getLogger(logger_name)
                paddle_logger.setLevel(logging.ERROR)
                paddle_logger.propagate = False

            # 禁用警告信息
            warnings.filterwarnings('ignore')

        try:
            # 初始化OCR
            self.ocr = PaddleOCR(
                use_gpu=True,
                lang='ch',
                show_log=self.show_ocr_log,  # 使用配置的show_ocr_log
                use_angle_cls=False,
                det=True,
                rec=True,
                det_algorithm='DB',
                det_limit_side_len=2240,
                det_limit_type='max',
                det_db_thresh=0.2,
                det_db_box_thresh=0.3,
                det_db_unclip_ratio=1.6,
                rec_algorithm='SVTR_LCNet',
                rec_batch_num=1,
                cls_batch_num=1,
                enable_mkldnn=True,
                cpu_threads=4,
                rec_char_type='ch',
                rec_model_dir="F:/2025Projects/1000Y/models/ch_PP-OCRv4_det",
                drop_score=0.5,
                use_space_char=True,
                det_box_thresh=0.7,
                det_unclip_ratio=1.3
            )
            self.logger.info("=========================文字识别器初始化完成=========================")
        except Exception as e:
            self.logger.error(f"文字识别器初始化失败: {e}")
            raise

    # 处理图像并识别文字
    def process_and_recognize(self, 
                            image: np.ndarray,
                            save_debug: bool = False,
                            debug_path: Optional[Path] = None,
                            timestamp: str = None) -> Dict:
        """处理图像并识别文字"""
        try:
            # 保存调试图像
            if save_debug and debug_path and timestamp:
                debug_dir = Path(debug_path)
                debug_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(debug_dir / f'{timestamp}.png'), image)
            
            # 执行OCR识别
            result = self.ocr.ocr(image, cls=False)
            
            if not result or not result[0]:
                return {'text': '', 'details': []}
                
            # 提取文本和坐标信息
            texts = []
            details = []
            for line in result[0]:
                box = line[0]
                text = line[1][0]
                confidence = line[1][1]
                
                # 确保文本是UTF-8编码
                if isinstance(text, bytes):
                    text = text.decode('utf-8')
                elif isinstance(text, str):
                    text = text.encode('utf-8').decode('utf-8')
                
                self.logger.debug(f"识别文本: {text}, 置信度: {confidence}")
                if confidence > 0.1:  # 降低置信度阈值
                    texts.append(text)
                    # 计算中心点坐标
                    center_x = int(sum(point[0] for point in box) / 4)
                    center_y = int(sum(point[1] for point in box) / 4)
                    details.append({
                        'text': text,
                        'confidence': confidence,
                        'box': box,
                        'center': (center_x, center_y)
                    })
            
            # 合并文本并确保是UTF-8编码
            result_text = " ".join(texts)
            result_text = result_text.encode('utf-8').decode('utf-8')
            
            return {
                'text': result_text,
                'details': details
            }
            
        except Exception as e:
            self.logger.error(f"文字识别出错: {str(e)}")
            return {'text': '', 'details': []}
    
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
            
            # 处理并识别
            text = self.process_and_recognize(
                image=region_image,
                save_debug=save_debug,
                debug_path=region_debug_path,
                timestamp=timestamp
            )
            
            results[region_name] = text
            self.logger.debug(f"区域 {region_name} 识别结果: {text}")
            
        return results 