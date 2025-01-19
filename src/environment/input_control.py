import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pynput import keyboard, mouse
import yaml
import math
import logging

class InputMonitor:
    """
    输入监控器类
    负责监控键盘和鼠标的输入事件，并记录到不同的记录集中
    """

    MODULE_NAME = 'InputMonitor'
    
    def __init__(self, action_config: Dict, save_dir: str, logger: logging.Logger):
        """
        初始化输入监控器
        
        Args:
            action_config: 动作配置字典
            save_dir: 数据保存目录
            logger: 日志记录器
        """ 
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<输入监控器初始化开始...>>>>>>>>>>>>>>>>>>")
        self.config = action_config
        # 三个不同的记录集
        self.raw_events: List[Dict] = []        # 原始记录
        self.processed_events: List[Dict] = []   # 处理后的记录
        self.mapped_actions: List[Dict] = []     # 映射后的动作
        self.current_keys = set()
        
        
        # 初始化保存目录
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化控制范围
        self.control_range = self.config['control_range']
        self.center_point = self.config['basic_actions']['move']['center_point']
        self.coordinate_ratio = self.config['basic_actions']['move']['coordinate_Screen_ratio']
        
        # 初始化键盘和鼠标监听器
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click
        )
        
        self.logger.info("InputMonitor initialized successfully")

    def start(self):
        """启动监听器"""
        self.keyboard_listener.start()
        self.mouse_listener.start()
        self.logger.info("Input monitoring started")

    def stop(self):
        """停止监听器"""
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        self.logger.info("Input monitoring stopped")

    def save_events(self):
        """保存所有记录集"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存原始记录
        raw_file = self.save_dir / f'raw_events_{timestamp}.json'
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(self.raw_events, f, ensure_ascii=False, indent=2)
        
        # 保存处理后的记录
        processed_file = self.save_dir / f'processed_events_{timestamp}.json'
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_events, f, ensure_ascii=False, indent=2)
        
        # 生成并保存动作映射
        self._generate_action_mappings()
        mapped_file = self.save_dir / f'mapped_actions_{timestamp}.json'
        with open(mapped_file, 'w', encoding='utf-8') as f:
            json.dump(self.mapped_actions, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"All event records saved to {self.save_dir}")

    def _on_key_press(self, key):
        """处理键盘按下事件"""
        try:
            # 添加调试日志
            self.logger.debug(f"原始按键: {key}, 类型: {type(key)}")
            
            # 统一按键处理
            if isinstance(key, keyboard.Key):
                key_char = key.name  # 处理特殊键
            elif isinstance(key, keyboard.KeyCode):
                # 对于 KeyCode，优先使用 char，如果没有则使用 vk
                if hasattr(key, 'char') and key.char:
                    key_char = key.char
                elif hasattr(key, 'vk') and key.vk:
                    # 数字键的 vk 码从 48(0) 开始
                    if 48 <= key.vk <= 57:  
                        key_char = str(key.vk - 48)  # 转换为字符串形式的数字
                    else:
                        key_char = str(key)
                else:
                    key_char = str(key)
            else:
                key_char = str(key)
            
            # 添加调试日志
            self.logger.debug(f"处理后的按键: {key_char}")
            
            # 处理功能键大写
            if key_char and isinstance(key_char, str) and key_char.startswith('f') and key_char[1:].isdigit():
                key_char = key_char.upper()
            
            # 修饰键映射
            modifier_map = {
                'ctrl_l': 'ctrl',
                'ctrl_r': 'ctrl',
                'shift_l': 'shift',
                'shift_r': 'shift',
                'alt_l': 'alt',
                'alt_r': 'alt'
            }
            
            # 统一修饰键名称
            if key_char in modifier_map:
                key_char = modifier_map[key_char]
            
            # 添加调试日志
            self.logger.debug(f"最终按键: {key_char}, 当前按键状态: {self.current_keys}")
            
            if self._is_valid_key(key_char) and key_char not in self.current_keys:
                # 记录原始事件
                raw_event = {
                    'timestamp': str(int(time.time() * 1000)),
                    'type': 'key_press',
                    'key': key_char
                }
                self.raw_events.append(raw_event)
                
                # 更新当前按键状态
                self.current_keys.add(key_char)
                
                # 检查是否是数字键且有修饰键
                is_number_key = key_char in self.config['key_mappings']['number_keys']
                has_modifier = bool(self.current_keys & {'ctrl', 'alt'})
                
                # 只有以下情况才记录到处理记录集
                if ((key_char.upper().startswith('F') and key_char[1:].isdigit()) or 
                    key_char == 'tab' or 
                    (is_number_key and has_modifier)):
                    
                    processed_event = raw_event.copy()
                    
                    # 如果是数字键且有修饰键，添加组合键信息
                    if is_number_key and has_modifier:
                        modifiers = self.current_keys & {'ctrl', 'alt'}
                        modifier = next(iter(modifiers))  # 获取第一个修饰键
                        combo_name = f"{modifier}_{key_char}"
                        
                        if combo_name in self.config['key_combo_dict']:
                            processed_event['combo'] = {
                                'type': 'combo',
                                'combo': combo_name,
                                'keys': [modifier, key_char]
                            }
                            self.logger.info(f"按键组合: {combo_name}")
                            # 添加到处理记录集
                            self.processed_events.append(processed_event)
                    else:
                        self.logger.info(f"功能键按下: {key_char}")
                        # 只有功能键才添加到处理记录集
                        if key_char.upper().startswith('F') or key_char == 'tab':
                            self.processed_events.append(processed_event)
                else:
                    if key_char in ['ctrl', 'shift', 'alt']:
                        self.logger.info(f"修饰键按下: {key_char}")
                    else:
                        self.logger.info(f"键盘按下: {key_char}")
        except Exception as e:
            self.logger.error(f"按键处理错误: {str(e)}, 按键: {key}")

    def _on_key_release(self, key):
        """处理键盘释放事件"""
        try:
            # 添加调试日志
            self.logger.debug(f"原始释放按键: {key}, 类型: {type(key)}")
            
            # 统一按键处理
            if isinstance(key, keyboard.Key):
                key_char = key.name  # 处理特殊键
            elif isinstance(key, keyboard.KeyCode):
                # 对于 KeyCode，优先使用 char，如果没有则使用 vk
                if hasattr(key, 'char') and key.char:
                    key_char = key.char
                elif hasattr(key, 'vk') and key.vk:
                    # 数字键的 vk 码从 48(0) 开始
                    if 48 <= key.vk <= 57:  
                        key_char = str(key.vk - 48)  # 转换为字符串形式的数字
                    else:
                        key_char = str(key)
                else:
                    key_char = str(key)
            else:
                key_char = str(key)
            
            # 添加调试日志
            self.logger.debug(f"处理后的释放按键: {key_char}")
            
            # 处理功能键大写
            if key_char and isinstance(key_char, str) and key_char.startswith('f') and key_char[1:].isdigit():
                key_char = key_char.upper()
            
            # 修饰键映射
            modifier_map = {
                'ctrl_l': 'ctrl',
                'ctrl_r': 'ctrl',
                'shift_l': 'shift',
                'shift_r': 'shift',
                'alt_l': 'alt',
                'alt_r': 'alt'
            }
            
            # 统一修饰键名称
            if key_char in modifier_map:
                key_char = modifier_map[key_char]
            
            # 添加调试日志
            self.logger.debug(f"最终释放按键: {key_char}, 当前按键状态: {self.current_keys}")
            
            if self._is_valid_key(key_char) and key_char in self.current_keys:
                # 记录原始事件
                raw_event = {
                    'timestamp': str(int(time.time() * 1000)),
                    'type': 'key_release',
                    'key': key_char
                }
                self.raw_events.append(raw_event)
                
                # 更新当前按键状态
                self.current_keys.discard(key_char)
                
                self.logger.info(f"键盘释放: {key_char}")
        except Exception as e:
            self.logger.error(f"按键释放处理错误: {str(e)}, 按键: {key}")

    def _is_valid_key(self, key: str) -> bool:
        """检查按键是否在有效范围内"""
        if not key:
            return False
        
        key_mappings = self.config['key_mappings']
        
        # 检查所有按键映射类型
        for mapping_type in ['function_keys', 'modifier_keys', 'number_keys', 'key_dict', 'mouse_buttons']:
            mapping = key_mappings.get(mapping_type, {})
            if key.lower() in mapping or key.upper() in mapping:
                return True
        
        return False

    def _on_mouse_click(self, x, y, button, pressed):
        """处理鼠标点击事件"""
        if not self._is_in_control_range(x, y):
            return

        button_name = button.name
        if button_name in self.config['key_mappings'].get('mouse_buttons', {}):
            # 转换状态名称为更直观的形式
            action_state = 'press' if pressed else 'release'
            
            # 创建原始事件
            raw_event = {
                'timestamp': str(int(time.time() * 1000)),
                'type': 'mouse_click',
                'button': f'Button.{button_name}',
                'state': action_state,
                'x': x,
                'y': y
            }
            # 记录原始事件
            self.raw_events.append(raw_event)
            
            # 只在按下时处理
            if action_state == 'press':
                if button_name == 'right':  # 右键点击计算移动方向
                    # 计算移动方向
                    direction_info = self._calculate_movement_direction(x, y)
                    if direction_info:
                        direction_name, keys = direction_info
                        movement_info = {
                            'direction': direction_name,
                            'keys': keys
                        }
                        
                        # 创建处理事件（包含移动信息）
                        processed_event = {
                            'timestamp': raw_event['timestamp'],
                            'type': 'mouse_click',
                            'button': raw_event['button'],
                            'state': 'press',
                            'x': x,
                            'y': y,
                            'movement': movement_info
                        }
                        self.processed_events.append(processed_event)
                        self.logger.info(f"鼠标右键移动: ({x}, {y}) -> 方向: {movement_info['direction']}")
                else:  # 左键点击
                    # 检查是否有组合键
                    combo_info = None
                    key_combo_dict = self.config.get('key_combo_dict', {})
                    
                    # 检查当前按键组合是否匹配配置的组合键
                    if 'shift' in self.current_keys and 'shift_mouse_click' in key_combo_dict:
                        combo_info = {
                            'type': 'combo',
                            'combo': 'shift_mouse_click',
                            'keys': ['shift', 'mouse_left_click']
                        }
                    elif 'ctrl' in self.current_keys and 'ctrl_mouse_click' in key_combo_dict:
                        combo_info = {
                            'type': 'combo',
                            'combo': 'ctrl_mouse_click',
                            'keys': ['ctrl', 'mouse_left_click']
                        }
                    
                    # 创建处理事件
                    processed_event = {
                        'timestamp': raw_event['timestamp'],
                        'type': 'mouse_click',
                        'button': raw_event['button'],
                        'state': 'press',
                        'x': x,
                        'y': y
                    }
                    
                    # 如果是组合键，添加组合键信息
                    if combo_info:
                        processed_event['combo'] = combo_info
                        self.logger.info(f"鼠标组合键点击: ({x}, {y}) -> {combo_info['combo']}")
                    else:
                        self.logger.info(f"鼠标左键点击: ({x}, {y})")
                    
                    self.processed_events.append(processed_event)
            else:
                self.logger.info(f"鼠标{button_name}键释放: ({x}, {y})")

    def _is_in_control_range(self, x: int, y: int) -> bool:
        """检查坐标是否在控制范围内"""
        range_x = self.control_range['x']
        range_y = self.control_range['y']
        return (range_x[0] <= x <= range_x[1] and 
                range_y[0] <= y <= range_y[1])

    def _calculate_movement_direction(self, x: int, y: int) -> Optional[Tuple[str, List[str]]]:
        """计算移动方向，返回(中文方向名称, 按键列表)"""
        dx = x - self.center_point[0]
        dy = self.center_point[1] - y  # 注意y轴方向是反的
        
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
            
        # 获取配置中的方向定义
        directions = self.config['basic_actions']['move']['directions']
        
        # 将角度映射到方向
        for direction_name, config in directions.items():
            angle_value = config['angle']
            # 考虑角度范围 (±22.5度)
            min_angle = (angle_value - 22.5) % 360
            max_angle = (angle_value + 22.5) % 360
            
            if min_angle <= angle <= max_angle or (min_angle > max_angle and (angle >= min_angle or angle <= max_angle)):
                # 返回中文方向名称和按键列表
                return direction_name, config['keys']
                
        return None

    def _map_movement_to_action(self, event: Dict):
        """将移动事件映射为动作"""
        if not event.get('movement'):
            return
        
        movement_keys = event['movement']['keys']
        timestamp = event['timestamp']
        
        # 获取动作标签
        action_label = self._get_movement_action_label(movement_keys)
        
        # 获取动作类型ID
        type_id = self.config['labels_dict']['move_actions']['type_id']
        
        mapped_action = {
            'timestamp': timestamp,
            'type': type_id,  # 使用 labels_dict 中定义的 type_id
            'key': action_label,  # 使用 actions 中定义的标签值
            'direction': event['movement']['direction'],  # 中文方向名称
            'position': {'x': event['x'], 'y': event['y']},
            'source': f"mouse_{event['button'].split('.')[-1]}_click"
        }
        self.mapped_actions.append(mapped_action)
        self.logger.info(f"移动动作映射: {event['movement']['direction']} ({','.join(movement_keys)})")

    def _get_movement_action_label(self, keys: List[str]) -> int:
        """获取移动动作的标签"""
        # 在 action_mapping 中查找对应的动作标签
        for action_id, key_list in self.config['action_mapping'].items():
            if isinstance(key_list, list) and sorted(key_list) == sorted(keys):
                return int(action_id)
        return -1

    def _map_to_action(self, event: Dict):
        """将事件映射为动作标签"""
        if event['type'] != 'key_press':
            return
        
        # 如果事件中包含组合键信息，直接使用
        if event.get('combo'):
            combo_name = event['combo']['combo']
            if combo_name in self.config['key_combo_dict']:
                action_label = self.config['key_combo_dict'][combo_name]
                type_id, action_name = self._get_action_type_info(action_label)
                
                mapped_action = {
                    'timestamp': event['timestamp'],
                    'type': type_id,
                    'key': action_label,
                    'direction': action_name,
                    'source': f'keyboard_combo_{combo_name}'
                }
                self.mapped_actions.append(mapped_action)
                self.logger.info(f"组合键动作映射: {action_name} ({combo_name})")
                return
        
        key = event['key']
        timestamp = event['timestamp']
        
        # 处理功能键和tab键
        if (key.upper().startswith('F') and key[1:].isdigit()) or key == 'tab':
            # 在 action_mapping 中查找对应的动作标签
            for action_id, key_list in self.config['action_mapping'].items():
                if isinstance(key_list, list) and key_list == [key]:
                    action_label = int(action_id)
                    # 获取动作类型ID和名称
                    type_id, action_name = self._get_action_type_info(action_label)
                    
                    mapped_action = {
                        'timestamp': timestamp,
                        'type': type_id,
                        'key': action_label,
                        'direction': action_name,
                        'source': f'keyboard_{key.lower()}'
                    }
                    self.mapped_actions.append(mapped_action)
                    self.logger.info(f"功能键动作: {action_name} ({key})")
                    return
        
        # 处理其他按键（组合键等）
        action_mapping = self.config['action_mapping']
        key_combo_dict = self.config.get('key_combo_dict', {})
        
        # 处理组合键
        current_combo = '+'.join(sorted(self.current_keys))
        if current_combo in key_combo_dict:
            action_label = key_combo_dict[current_combo]
            type_id, action_name = self._get_action_type_info(action_label)
            mapped_action = {
                'timestamp': timestamp,
                'type': type_id,
                'key': action_label,
                'direction': action_name,
                'source': f'keyboard_combo_{current_combo}'
            }
            self.mapped_actions.append(mapped_action)
            self.logger.info(f"组合键动作: {action_name} ({current_combo})")

    def _map_mouse_combo_action(self, event: Dict):
        """处理鼠标组合键动作"""
        combo = event['combo']['combo']  # 获取组合键名称（如 'shift_mouse_click'）
        
        # 查找对应的动作标签
        if combo in self.config.get('key_combo_dict', {}):
            action_label = self.config['key_combo_dict'][combo]
            # 获取动作类型ID和名称
            type_id, action_name = self._get_action_type_info(action_label)
            
            mapped_action = {
                'timestamp': event['timestamp'],
                'type': type_id,
                'key': action_label,
                'direction': action_name,
                'position': {'x': event['x'], 'y': event['y']},
                'source': f"mouse_{event['button'].split('.')[-1]}_click"
            }
            self.mapped_actions.append(mapped_action)
            self.logger.info(f"鼠标组合动作: {action_name} ({combo})")

    def _get_action_type_info(self, action_label: int) -> Tuple[int, str]:
        """获取动作的类型ID和名称"""
        for action_type, type_info in self.config['labels_dict'].items():
            actions = type_info.get('actions', {})
            for name, label in actions.items():
                if label == action_label:
                    return type_info['type_id'], name
        return -1, "unknown"

    def _map_mouse_click_to_action(self, event: Dict):
        """将鼠标点击事件映射为动作"""
        button = event['button'].replace('Button.', '')
        timestamp = event['timestamp']
        
        if button == 'left':  # 左键点击映射为选定目标
            try:
                # 从 labels_dict 中获取选定目标的类型ID和标签
                target_actions = self.config['labels_dict'].get('target_actions')
                if not target_actions:
                    self.logger.error("配置文件中缺少 target_actions 定义")
                    return
                
                type_id = target_actions['type_id']
                action_label = target_actions['actions'].get('选定目标', -1)
                
                mapped_action = {
                    'timestamp': timestamp,
                    'type': type_id,
                    'key': action_label,
                    'direction': '选定目标',
                    'position': {'x': event['x'], 'y': event['y']},
                    'source': 'mouse_left_click'
                }
                self.mapped_actions.append(mapped_action)
                self.logger.info(f"鼠标左键动作: 选定目标 ({event['x']}, {event['y']})")
            except KeyError as e:
                self.logger.error(f"配置错误: {str(e)}")
            except Exception as e:
                self.logger.error(f"映射鼠标点击动作时出错: {str(e)}")
        
        elif button == 'right' and event.get('movement'):  # 右键移动
            self._map_movement_to_action(event)

    def _generate_action_mappings(self):
        """根据处理记录集生成动作映射"""
        self.mapped_actions.clear()
        for event in self.processed_events:
            if event['type'] == 'mouse_click':
                if event.get('combo'):  # 先检查是否是组合键
                    self._map_mouse_combo_action(event)
                elif event.get('movement'):  # 再检查是否是移动
                    self._map_movement_to_action(event)
                else:  # 最后才是普通点击
                    self._map_mouse_click_to_action(event)
            else:  # key_press
                self._map_to_action(event)
