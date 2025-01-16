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
            'active_skills': self._process_active_skills,  # 激活技能
            'char_coordinates': self._process_char_coordinates,  # 角色坐标  
            'char_vitality': self._preprocess_char_vitality,  # 角色活力值
            'char_neigong': self._preprocess_neigong_area,  # 角色内功值
            'char_head': self._preprocess_char_head,  # 角色头防值
            'char_hand': self._preprocess_char_hand,  # 角色手防值
            'char_foot': self._preprocess_char_foot,  # 角色脚防值  
            'char_qigong': self._preprocess_char_qigong,  # 角色元气值
            'skill_exp_min': self._preprocess_skill_exp_min,  # 技能小经验值
            'skill_exp_max': self._preprocess_skill_exp_max,  # 技能大经验值
            'target_panel': self._preprocess_target_panel,  # 目标面板
            'target_hp': self._preprocess_target_hp,  # 目标血量
            'target_name': self._preprocess_target_name,  # 目标名字
            'nearby_monster_name_1': self._preprocess_nearby_monster_name_1,  # 近身寻怪名区域-1
            'nearby_monster_name_2': self._preprocess_nearby_monster_name_1,  # 近身寻怪名区域-2
            'char_revival': self._preprocess_char_revival,  # 角色复活信息
            'char_eat_food': self._preprocess_char_eat_food,  # 角色食物状态

        }   
        self.logger.info("=========================数据处理器初始化完成=========================")
    
    # 角色食物状态
    def _preprocess_char_eat_food(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """角色食物状态
        
        处理三种状态：
        1. 检测到"服用了XXX。" - 返回 {'status': True, 'count': N, 'state': 'open', 'item_name': 'XXX'}
        2. 检测到"无法服用。" - 返回 {'status': True, 'count': N, 'state': 'close', 'item_name': ''}
        3. 未检测到任何文字 - 返回 {'status': False, 'item_name': ''}
        """
        try:
            if not ocr_result or not isinstance(ocr_result, dict) or 'details' not in ocr_result:
                return {'status': False}
            
            self.logger.debug("=== 食物状态OCR结果 ===")
            self.logger.debug(f"原始OCR结果: {repr(ocr_result)}")
            
            # 存储每行文本及其y坐标
            text_boxes = []
            
            # 同一行文本的y坐标差异阈值
            Y_THRESHOLD = 10
            X_GAP_THRESHOLD = 30  # 水平方向上允许的最大间隔
            
            # 收集所有文本框
            for detail in ocr_result['details']:
                text = detail['text'].strip()
                if text:
                    box = detail['box']
                    center_y = sum(point[1] for point in box) / 4
                    left_x = min(point[0] for point in box)
                    right_x = max(point[0] for point in box)
                    text_boxes.append({
                        'text': text,
                        'center_y': center_y,
                        'left_x': left_x,
                        'right_x': right_x,
                        'box': box
                    })
            
            # 按y坐标排序
            text_boxes.sort(key=lambda x: x['center_y'])
            
            # 合并同一行的文本
            merged_lines = []
            current_line = []
            current_y = None
            
            for i, box in enumerate(text_boxes):
                if current_y is None:
                    current_y = box['center_y']
                    current_line.append(box)
                else:
                    # 检查y坐标是否在阈值范围内
                    if abs(box['center_y'] - current_y) <= Y_THRESHOLD:
                        # 检查x方向上的间隔
                        if current_line:
                            last_box = current_line[-1]
                            if box['left_x'] - last_box['right_x'] <= X_GAP_THRESHOLD:
                                current_line.append(box)
                            else:
                                # 处理当前行
                                if current_line:
                                    current_line.sort(key=lambda x: x['left_x'])
                                    line_text = ''.join(item['text'] for item in current_line)
                                    merged_lines.append(line_text)
                                # 开始新的一行
                                current_line = [box]
                        else:
                            current_line.append(box)
                    else:
                        # 处理当前行
                        if current_line:
                            current_line.sort(key=lambda x: x['left_x'])
                            line_text = ''.join(item['text'] for item in current_line)
                            merged_lines.append(line_text)
                        # 开始新的一行
                        current_line = [box]
                        current_y = box['center_y']
            
            # 处理最后一行
            if current_line:
                current_line.sort(key=lambda x: x['left_x'])
                line_text = ''.join(item['text'] for item in current_line)
                merged_lines.append(line_text)
            
            # 服用药品的模式匹配
            use_patterns = [
                r'(?:[品服使][用]了?|吃了?)(.*?)(?:。|\s)*$',  # 匹配更多变体
                r'(?:成功)?(?:服|使|品)?用了?(.*?)(?:。|\s)*$'  # 更宽松的匹配
            ]
            
            # 无法服用的模式匹配
            cannot_use_patterns = [
                r'(?:暂时)?(?:[无不][法能]|不可)(?:再|继续)?[服使品][用](?:。|\s)*$',  # 匹配更多变体
                r'(?:已经)?(?:不能|无法)(?:再|继续)?(?:服|使|品)?用(?:。|\s)*$'  # 更宽松的匹配
            ]
            
            use_count = 0
            cannot_use_count = 0
            item_names = []
            state = None  # 初始化状态变量
            
            for line in merged_lines:
                self.logger.debug(f"处理合并后的文本行: {line}")
                
                # 检查是否无法服用
                for pattern in cannot_use_patterns:
                    if re.search(pattern, line):
                        cannot_use_count += 1
                        state = 'close'  # 设置状态为close
                        break
                
                # 如果还没有设置状态，检查是否服用了物品
                if state != 'close':
                    for pattern in use_patterns:
                        match = re.search(pattern, line)
                        if match:
                            use_count += 1
                            item_name = match.group(1).strip()
                            if item_name:
                                item_names.append(item_name)
                            state = 'open'  # 设置状态为open
                            break
            
            # 根据状态返回结果
            if state:  # 如果状态被设置（说明检测到了相关文本）
                return {
                    'status': True,
                    'state': state,
                    'count': use_count,
                    'item_name': item_names
                }
            
            return {'status': False}  # 未检测到任何文字时只返回状态
                
        except Exception as e:
            self.logger.error(f"处理食物状态出错: {str(e)}")
            return {'status': False}  # 发生异常时只返回状态
    
    # 角色复活信息预处理
    def _preprocess_char_revival(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """角色复活信息预处理
        
        处理格式如: "剩下30秒重新站立" 或类似变体
        返回格式: {'char_revival': bool, 'time': int}
        """
        try:
            if not ocr_result:
                return {'char_revival': False}
            
            self.logger.debug("=== 复活信息OCR结果 ===")
            self.logger.debug(f"原始OCR结果: {repr(ocr_result)}")
            
            # 存储每行文本及其y坐标
            text_boxes = []
            
            # 同一行文本的y坐标差异阈值
            Y_THRESHOLD = 10
            
            if isinstance(ocr_result, dict) and 'details' in ocr_result:
                # 收集所有文本框
                for detail in ocr_result['details']:
                    text = detail['text'].strip()
                    if text:
                        box = detail['box']
                        center_y = sum(point[1] for point in box) / 4
                        left_x = min(point[0] for point in box)
                        text_boxes.append({
                            'text': text,
                            'center_y': center_y,
                            'left_x': left_x
                        })
                
                # 按y坐标排序
                text_boxes.sort(key=lambda x: x['center_y'])
                
                # 合并同一行的文本
                merged_lines = []
                current_line = []
                current_y = None
                
                for box in text_boxes:
                    if current_y is None:
                        current_y = box['center_y']
                        current_line.append(box)
                    else:
                        if abs(box['center_y'] - current_y) <= Y_THRESHOLD:
                            current_line.append(box)
                        else:
                            # 处理当前行
                            if current_line:
                                current_line.sort(key=lambda x: x['left_x'])
                                line_text = ' '.join(item['text'] for item in current_line)
                                merged_lines.append(line_text)
                            # 开始新的一行
                            current_line = [box]
                            current_y = box['center_y']
                
                # 处理最后一行
                if current_line:
                    current_line.sort(key=lambda x: x['left_x'])
                    line_text = ' '.join(item['text'] for item in current_line)
                    merged_lines.append(line_text)
                
                # 对每一行进行模式匹配
                min_time = 999
                patterns = [
                    r'剩[下余]?(\d+)秒.*站立',  # 标准格式
                    r'剩[下余]?(\d+)秒',        # 简短格式
                    r'(\d+)秒.*站立',           # 变体格式1
                    r'(\d+)秒.*站',             # 变体格式2
                ]
                
                for line in merged_lines:
                    self.logger.debug(f"处理文本行: {line}")
                    # 移除所有标点符号，保留空格
                    cleaned_line = re.sub(r'[^\w\s]', '', line)
                    
                    for pattern in patterns:
                        match = re.search(pattern, cleaned_line)
                        if match:
                            seconds = int(match.group(1))
                            if 0 <= seconds <= 30:  # 合理的秒数范围
                                min_time = min(min_time, seconds)
                                self.logger.debug(f"匹配到复活时间: {seconds}秒")
                                break
                
                if min_time != 999:
                    return {'char_revival': True, 'time': min_time}
            
            return {'char_revival': False}
            
        except Exception as e:
            self.logger.error(f"处理复活信息出错: {str(e)}")
            return {'char_revival': False}
    
    # 近身寻怪名区域-1
    def _preprocess_nearby_monster_name_1(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """近身寻怪名区域-1"""
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
                        # 使用OCR返回的中心点坐标
                        center_x, center_y = detail['center']
                        # 从配置中获取裁切区域坐标
                        x_offset, y_offset, width, height = self.area_config[self.current_region_name]['screen_split']['coordinates']
                        
                        # 计算在原图中的真实坐标
                        real_center_x = center_x + x_offset
                        real_center_y = center_y + y_offset
                        
                        # 更新中心点坐标为原图坐标
                        center_x, center_y = real_center_x, real_center_y
                        
                        self.logger.debug(f"裁切图中坐标: {cleaned_text}-({center_x-x_offset}, {center_y-y_offset})")
                        self.logger.debug(f"原图真实坐标: {cleaned_text}-({center_x}, {center_y})")

                        name_groups.append({
                            'text': cleaned_text,
                            'center_x': center_x,
                            'center_y': center_y
                        })
            
            self.logger.debug(f"最终结果: {name_groups}")
            return {'name_groups': name_groups}  
        except Exception as e:
            self.logger.error(f"处理游戏区域数据出错: {str(e)}")
            return {'name_groups': ''}
        
    # 目标名字处理
    def _preprocess_target_name(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """目标名字处理"""
        try:
            self.logger.debug(f"OCR结果: {ocr_result}")
            # 获取OCR结果中的第一行文本
            texts = []
            if isinstance(ocr_result, dict) and 'details' in ocr_result:
                for detail in ocr_result['details']:
                    if 'text' in detail:
                        text = detail['text'].strip()
                        if text:
                            texts.append(text)

                return {'target_name': texts[0]}
            else:
                self.logger.warning("OCR结果为空")
                return {'target_name': '无目标'}    
        except Exception as e:
            self.logger.error(f"处理目标名字出错: {str(e)}")
            return {'target_name': '无目标'}

    # 目标血量值处理
    def _preprocess_target_hp(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """目标血量值处理"""
        """
        计算血量百分比
        
        Args:
            binary_image: 二值化后的图像（黑色区域代表血量）
            
        Returns:
            health_percentage: 血量百分比
            stats: 包含计算过程中的统计信息的字典
        """
        height, width = image.shape
        center_y = height // 2
        sample_height = height
        start_y = center_y - sample_height//2
        end_y = center_y + sample_height//2

        # 统计有效列（寻找黑色像素）
        red_columns = 0
        valid_columns = []
        for x in range(width):
            column = image[start_y:end_y, x]
            if np.any(column == 0):  # 修改这里，寻找黑色像素
                red_columns += 1
                valid_columns.append(x)

        # 计算血量百分比
        if valid_columns:
            leftmost = min(valid_columns)
            rightmost = max(valid_columns)
            health_percentage = ((rightmost - leftmost + 1) / width) * 100
        else:
            health_percentage = 0
            leftmost = rightmost = 0
            
        return {'target_hp': round(health_percentage)}   
    
    # 目标面板预处理
    def _preprocess_target_panel(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """目标面板预处理"""

        try:
            # 读取目标图片（小图）和源图片（大图）
            template_path = "F:/2025Projects/1000Y//data/image/target_panel.png"
            template = cv2.imread(template_path)

            if template is None or image is None:
                print("无法读取图片，请检查路径")
                exit()

            # 执行模板匹配
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

            # 获取最佳匹配位置和匹配度
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 判断是否匹配成功
            if max_val >= 0.9:
                return {'target_panel_status': True, 'target_panel_match_rate': round(max_val, 2)} 
            else:
                return {'target_panel_status': False, 'target_panel_match_rate': round(max_val, 2)} 
            
        except Exception as e:
            self.logger.error(f"处理目标面板出错: {str(e)}")
            return {'target_panel_status': False}  
    
    # 处理技能经验_1
    def _preprocess_skill_exp_min(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """技能小经验值"""
        try:
            # 技能小经验值
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算小经验百分比
            skill_exp_min = round((first_black_x + 1) / width * 100)  # 取整
            self.logger.debug(f"技能小经验值: {skill_exp_min}")
            if skill_exp_min == 100:
                skill_exp_min =0
            return {'skill_exp_min': skill_exp_min}
        except Exception as e:
            self.logger.error(f"处理技能小经验值出错: {str(e)}")
            return {"skill_exp_1": 0} 
              
    # 处理技能经验_2
    def _preprocess_skill_exp_max(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """技能大经验值"""
        try:
            # 技能大经验值
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算大经验百分比
            skill_exp_max = round((first_black_x + 1) / width * 100, 4)  # 保留2位小数
            skill_exp_max = round(skill_exp_max/10)
            self.logger.debug(f"技能大经验值: {skill_exp_max}")
            if skill_exp_max >= 10:
                skill_exp_max =0
            return {'skill_exp_max': skill_exp_max}
        except Exception as e:
            self.logger.error(f"处理技能大经验值出错: {str(e)}")
            return {"skill_exp_max": 0}
  
    # 处理角色元气值
    def _preprocess_char_qigong(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理角色元气值"""
        try:
            # 角色角色元气值
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算脚防百分比
            char_qigong = round((first_black_x + 1) / width * 100)  # 取整
            self.logger.debug(f"角色元气值: {char_qigong}")
            return {'char_qigong': char_qigong}
        except Exception as e:
            self.logger.error(f"处理角色元气值出错: {str(e)}")
            return {"char_qigong": 0}        
    
    # 处理角色脚防值
    def _preprocess_char_foot(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:

        
        """处理角色脚防值"""
        try:
            # 角色脚防值
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算脚防百分比
            char_foot = round((first_black_x + 1) / width * 100)  # 取整
            self.logger.debug(f"角色脚防值: {char_foot}")
            return {'foot': char_foot}
        except Exception as e:
            self.logger.error(f"处理角色脚防值出错: {str(e)}")
            return {"foot": 0}         
    
    
     # 处理角色手防值
    
    # 处理角色手防值
    def _preprocess_char_hand(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理角色手防值"""
        try:
            # 角色手防值
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算手防百分比
            char_hand = round((first_black_x + 1) / width * 100)  # 取整
            self.logger.debug(f"角色手防值: {char_hand}")
            return {'hand': char_hand}
        except Exception as e:
            self.logger.error(f"处理角色手防值出错: {str(e)}")
            return {"hand": 0}  
    
    # 处理角色头防值
    def _preprocess_char_head(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理角色头防值"""
        try:
            # 步骤1：计算头防
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算头防百分比
            char_head = round((first_black_x + 1) / width * 100)  # 取整
            self.logger.debug(f"角色头防值: {char_head}")
            return {'head': char_head}
        except Exception as e:
            self.logger.error(f"处理角色头防值出错: {str(e)}")
            return {"head": 0}
    
    # 处理角色内功值
    def _preprocess_neigong_area(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理角色内功值"""
        try:
            # 步骤1：计算内功
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算内功百分比
            char_neigong = round((first_black_x + 1) / width * 100)  # 取整
            self.logger.debug(f"角色内功值: {char_neigong}")
            return {'mp': char_neigong}
        except Exception as e:
            self.logger.error(f"处理角色内功值出错: {str(e)}")
            return {"mp": 0}
    
    # 处理角色活力值
    def _preprocess_char_vitality(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理角色活力值"""
        try:
            # 步骤1：计算血量
            # 获取图像中心行
            center_y = image.shape[0] // 2
            center_row = image[center_y]

            # 从右向左查找第一个黑色像素点
            width = image.shape[1]
            first_black_x = width - 1
            for x in range(width-1, -1, -1):
                if center_row[x] == 0:  # 0表示黑色
                    first_black_x = x
                    break
            # 计算血量百分比
            char_vitality = round((first_black_x + 1) / width * 100)  # 取整
            self.logger.debug(f"角色活力值: {char_vitality}")
            return {'hp': char_vitality}
        except Exception as e:
            self.logger.error(f"处理角色活力值出错: {str(e)}")
            return {"hp": 0}   

    # 处理角色坐标
    def _process_char_coordinates(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理角色坐标
        
        处理以下格式：
        1. "87:84" - 标准格式
        2. "87 84" - 无冒号分隔
        3. ["87", "84"] - 分开的两段文本
        """
        try:    
            if not ocr_result or image is None:
                return {'x': 0, 'y': 0}
            
            self.logger.debug("=== 角色坐标OCR结果 ===")
            self.logger.debug(f"原始OCR结果: {repr(ocr_result)}")
            
            # 存储所有识别到的文本
            texts = []
            if isinstance(ocr_result, dict) and 'details' in ocr_result:
                for detail in ocr_result['details']:
                    if 'text' in detail:
                        text = detail['text'].strip()
                        if text:
                            texts.append(text)
            
            if not texts:
                return {'x': 0, 'y': 0}
            
            # 处理不同情况
            if len(texts) == 1:
                # 单个文本的情况
                text = texts[0]
                if ':' in text:
                    # 标准格式 "87:84"
                    x, y = text.split(':')
                else:
                    # 可能是空格分隔 "87 84"
                    parts = text.split()
                    if len(parts) == 2:
                        x, y = parts
                    else:
                        return {'x': 0, 'y': 0}
            elif len(texts) == 2:
                # 两段分开的文本
                x, y = texts
                # 组合成标准格式
                text = f"{x}:{y}"
                self.logger.debug(f"组合分散的坐标文本: {text}")
            else:
                self.logger.warning(f"无法处理的坐标文本格式: {texts}")
                return {'x': 0, 'y': 0}
            
            # 尝试转换为整数
            try:
                x = int(x.strip())
                y = int(y.strip())
                self.logger.debug(f"识别到坐标: X={x}, Y={y}")
                return {'x': x, 'y': y}
            except (ValueError, TypeError):
                self.logger.error(f"坐标转换失败: x={x}, y={y}")
                return {'x': 0, 'y': 0}
            
        except Exception as e:
            self.logger.error(f"处理角色坐标出错: {str(e)}")
            return {'x': 0, 'y': 0}

    # 处理激活技能
    def _process_active_skills(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理激活技能
        
        Args:
            ocr_result: PaddleOCR的识别结果
            image: 原始图像数据
            
        Returns:
            Dict[str, Any]: 处理后的技能数据，包含行数、技能列表和合并后的文本
        """
        try:
            if not ocr_result or image is None:
                return {}
            
            self.logger.debug("=== 激活技能OCR结果 ===")
            self.logger.debug(f"原始OCR结果: {repr(ocr_result)}")
            
            # 存储每行文本及其y坐标
            text_lines = []
            
            # 判断同一行的阈值（y坐标差异在这个范围内认为是同一行）
            Y_THRESHOLD = 10
            
            if isinstance(ocr_result, dict) and 'details' in ocr_result:
                # 先收集所有文本框及其位置信息
                text_boxes = []
                for detail in ocr_result['details']:
                    text = detail['text'].strip()
                    if text:
                        # 使用OCR返回的box信息
                        box = detail['box']
                        # 计算中心y坐标
                        center_y = sum(point[1] for point in box) / 4
                        # 获取左边界x坐标
                        left_x = min(point[0] for point in box)
                        text_boxes.append({
                            'text': text,
                            'center_y': center_y,
                            'left_x': left_x
                        })
                
                # 按y坐标排序
                text_boxes.sort(key=lambda x: x['center_y'])
                
                # 合并同一行的文本
                current_line = []
                current_y = None
                
                for box in text_boxes:
                    if current_y is None:
                        current_y = box['center_y']
                        current_line.append(box)
                    else:
                        # 判断是否属于同一行
                        if abs(box['center_y'] - current_y) <= Y_THRESHOLD:
                            current_line.append(box)
                        else:
                            # 当前文本框属于新的一行，处理之前的行
                            # 按x坐标排序并合并文本
                            current_line.sort(key=lambda x: x['left_x'])
                            line_text = ' '.join(item['text'] for item in current_line)
                            text_lines.append(line_text)
                            # 开始新的一行
                            current_line = [box]
                            current_y = box['center_y']
                
                # 处理最后一行
                if current_line:
                    current_line.sort(key=lambda x: x['left_x'])
                    line_text = ' '.join(item['text'] for item in current_line)
                    text_lines.append(line_text)
            
            # 合并所有行
            combined_text = '|'.join(text_lines)
            skill_count = len(text_lines)
            
            self.logger.debug(f"共识别到 [{skill_count}] 个技能-处理后的技能列表:\n{combined_text}")
            
            if skill_count > 10:  # 假设技能数量不应该超过10个
                self.logger.warning(f"识别到 [{skill_count}] 个技能，可能存在问题")
            
            return {
                'row_num': skill_count,
                'active_skills': text_lines,  # 保持键名一致，虽然这里是技能列表
                'all_active_skills': combined_text
            }
            
        except Exception as e:
            self.logger.error(f"处理激活技能出错: {str(e)}")
            return {}
    
    # 处理聊天消息
    def _process_chat(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理聊天消息
        
        Args:
            ocr_result: PaddleOCR的识别结果
            image: 原始图像数据
            
        Returns:
            Dict[str, Any]: 处理后的聊天消息数据，包含行数、消息列表和合并后的文本
        """
        try:
            if not ocr_result or image is None:
                return {}
            
            self.logger.debug("=== 聊天区域OCR结果 ===")
            self.logger.debug(f"原始OCR结果: {repr(ocr_result)}")
            
            # 存储每行文本及其y坐标
            text_lines = []
            
            # 判断同一行的阈值（y坐标差异在这个范围内认为是同一行）
            Y_THRESHOLD = 10
            
            if isinstance(ocr_result, dict) and 'details' in ocr_result:
                # 先收集所有文本框及其位置信息
                text_boxes = []
                for detail in ocr_result['details']:
                    text = detail['text'].strip()
                    if text:
                        # 使用OCR返回的box信息
                        box = detail['box']
                        # 计算中心y坐标
                        center_y = sum(point[1] for point in box) / 4
                        # 获取左边界x坐标
                        left_x = min(point[0] for point in box)
                        text_boxes.append({
                            'text': text,
                            'center_y': center_y,
                            'left_x': left_x
                        })
                
                # 按y坐标排序
                text_boxes.sort(key=lambda x: x['center_y'])
                
                # 合并同一行的文本
                current_line = []
                current_y = None
                
                for box in text_boxes:
                    if current_y is None:
                        current_y = box['center_y']
                        current_line.append(box)
                    else:
                        # 判断是否属于同一行
                        if abs(box['center_y'] - current_y) <= Y_THRESHOLD:
                            current_line.append(box)
                        else:
                            # 当前文本框属于新的一行，处理之前的行
                            # 按x坐标排序并合并文本
                            current_line.sort(key=lambda x: x['left_x'])
                            line_text = ' '.join(item['text'] for item in current_line)
                            text_lines.append(line_text)
                            # 开始新的一行
                            current_line = [box]
                            current_y = box['center_y']
                
                # 处理最后一行
                if current_line:
                    current_line.sort(key=lambda x: x['left_x'])
                    line_text = ' '.join(item['text'] for item in current_line)
                    text_lines.append(line_text)
            
            # 合并所有行
            combined_text = '\n'.join(text_lines)
            message_count = len(text_lines)
            
            self.logger.debug(f"共识别到 [{message_count}] 行聊天消息-处理后的聊天消息:\n{combined_text}")
            
            if message_count > 5:
                self.logger.warning(f"识别到 [{message_count}] 行聊天消息，可能存在问题")
            
            return {
                'row_num': message_count,
                'messages': text_lines,
                'combined_text': combined_text
            }
            
        except Exception as e:
            self.logger.error(f"处理聊天消息出错: {str(e)}")
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
                        # 使用OCR返回的中心点坐标
                        center_x, center_y = detail['center']
                        # 从配置中获取裁切区域坐标
                        x_offset, y_offset, width, height = self.area_config['game_area']['screen_split']['coordinates']
                        
                        # 计算在原图中的真实坐标
                        real_center_x = center_x + x_offset
                        real_center_y = center_y + y_offset
                        
                        # 更新中心点坐标为原图坐标
                        center_x, center_y = real_center_x, real_center_y
                        
                        self.logger.debug(f"裁切图中坐标: {cleaned_text}-({center_x-x_offset}, {center_y-y_offset})")
                        self.logger.debug(f"原图真实坐标: {cleaned_text}-({center_x}, {center_y})")

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
         
    # 处理面板区域数据
    def _process_panel_area(self, ocr_result: Dict, image: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """处理面板区域数据"""
        try:
            # 检查OCR结果格式并获取文本
            if (isinstance(ocr_result, dict) and 
                'details' in ocr_result and 
                len(ocr_result['details']) > 0):
                # 获取第一个检测到的文本（面板区域通常只有一行时间文本）
                full_text = ocr_result['details'][0]['text']
            else:
                return {'date': 0, 'time': 0, 'ms': 0}
            
            # 使用正则表达式匹配时间格式
            pattern = r"(\d+\]:)?(?P<date>\d{4}/\d{1,2}/\d{1,2})\s?(?P<time>\d{1,2}:\d{2}:\d{2})[/\(\[]?(?P<ms>\d+)ms[\)\]\}]?"
            match = re.match(pattern, full_text)
            if match:
                date = match.group("date")
                time = match.group("time")
                ms = match.group("ms")
                self.logger.debug(f"识别到数据: {date}, {time}, {ms}")
                return {'date': date, 'time': time, 'ms': int(ms)}
            
        except Exception as e:
            self.logger.error(f"处理面板区域数据出错: {str(e)}")
        
        self.logger.warning(f"没有识别到数据")    
        return {'date': 0, 'time': 0, 'ms': 0}
                    
    # 处理单个区域的数据
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
                # self.logger.debug(f"区域 {region_name} 处理结果: {return_data}")
                return return_data
            # 如果没有特定的处理方法，返回原始OCR结果
            self.logger.warning(f"区域 {region_name} 无特定处理方法，返回原始结果")
            return ocr_result if isinstance(ocr_result, dict) else {'text': str(ocr_result)} if ocr_result else {}
                
        finally:
            self.current_region_name = None
            self.current_region_config = None 