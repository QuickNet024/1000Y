# -*- coding: utf-8 -*-
"""
动作执行器模块

该模块负责:
1. 键盘动作执行
2. 鼠标动作执行
3. 动作序列管理
4. 动作执行状态跟踪

作者: QuickNet
日期: 2024-01
"""

from pathlib import Path
import time
import keyboard
import win32api
import win32con
import logging
from typing import Dict, List, Union, Tuple, Optional, Any
import yaml
import math
import json
from datetime import datetime
from collections import deque
from dataclasses import dataclass

from src.utils.config_manager import ConfigManager
from src.utils.logger_manager import LoggerManager


# 动作执行器类
class ActionExecutor:
    """
    动作执行器类
    
    负责执行键盘和鼠标动作，支持:
    1. 单次按键
    2. 组合键
    3. 鼠标移动
    4. 鼠标点击
    5. 动作序列执行
    
    属性:
        MODULE_NAME (str): 模块名称
        logger (Logger): 日志记录器
        basic_config (dict): 基础配置
    """
    
    MODULE_NAME = 'ActionExecutor'
    
    @dataclass
    class ActionRecord:
        """动作记录数据类"""
        timestamp: float
        action_type: str
        action_name: str
        params: Dict[str, Any]
        result: bool
        game_state: Optional[Dict] = None

    def __init__(self, 
                 config_manager: ConfigManager,          # 必需参数先写
                 logger: Optional[logging.Logger] = None): # 可选参数后写
        """
        初始化动作执行器
        
        Args:
            logger: 日志记录器
            config_manager: 配置管理器实例
        """
        # 初始化配置管理器
        self.config_manager = config_manager   

        self.logger_config = self.config_manager.get_logger_config()
        self.basic_config = self.config_manager.basic_config
        self.action_config = self.config_manager.action_config
        self.logger = LoggerManager(
            name=self.MODULE_NAME,
            **self.logger_config
        ).get_logger()

        # 加载动作配置
        self.game_id = self.action_config.get('game_id')
        self.game_name = self.action_config.get('game_name')
        # 获取控制范围
        self.control_range = self.action_config.get('control_range')

        # 根据配置初始化动作映射
        self._init_action_mappings()
        
        self.logger.info(f"动作执行器初始化完成 - 游戏: {self.game_id}")
        
        
        # 初始化动作记录
        self.recording_enabled = self.action_config['action_recording']['enabled']
        if self.recording_enabled:
            self._init_action_recording()
            
        # 初始化动作空间(为强化学习准备)
        self._init_action_space()
        
    def _load_action_config(self, config_path: str) -> dict:
        """加载动作配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"成功加载动作配置: {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"加载动作配置失败: {e}")
            raise

    def _init_action_mappings(self):
        """初始化动作映射"""
        # 获取移动配置
        move_config = self.action_config['basic_actions']['move']
        self.move_type = move_config['type']
        
        if self.move_type == 'mouse':
            self.center_point = move_config['center_point']
            self.move_radius = move_config['radius']
            # 初始化鼠标移动相关方法
            self._init_mouse_move_actions()
        else:
            # 初始化键盘移动相关方法
            self._init_keyboard_move_actions()
        
        # 初始化技能映射
        self.skill_bindings = self.action_config['basic_actions']['skills']['bindings']
        
        # 初始化物品映射
        self.item_bindings = self.action_config['basic_actions']['items']['bindings']

    def _init_mouse_move_actions(self):
        """
        初始化鼠标移动动作映射
        
        从配置文件加载:
        - 八个方向的角度值
        - 中心点坐标
        - 移动半径
        """
        directions = self.action_config['basic_actions']['move']['directions']
        # 修改键名以匹配中文配置
        self.direction_angles = {
            '上': 90,
            '右上': 45,
            '右': 0,
            '右下': 315,
            '下': 270,
            '左下': 225,
            '左': 180,
            '左上': 135
        }

    def _init_keyboard_move_actions(self):
        """初始化键盘移动动作"""
        directions = self.action_config['basic_actions']['move']['directions']
        self.direction_keys = {
            name: data['keys'] 
            for name, data in directions.items()
        }
 
    def press_key(self, key: str, duration: float = 0.1):
        """
        按下并释放按键
        
        Args:
            key: 按键名称
            duration: 按住时长(秒)
        """
        try:
            keyboard.press(key)
            time.sleep(duration)
            keyboard.release(key)
            self.logger.debug(f"执行按键: {key}, 持续时间: {duration}秒")
        except Exception as e:
            self.logger.error(f"按键执行失败 {key}: {e}")
                
    def press_combination(self, keys: List[str], duration: float = 0.1):
        """
        执行组合键
        
        Args:
            keys: 按键列表，如 ['ctrl', 'c'] 表示Ctrl+C
            duration: 按住时长(秒)
            
        Returns:
            bool: 执行是否成功
            
        示例:
            >>> action_executor.press_combination(['ctrl', 'c'])  # 执行Ctrl+C
            >>> action_executor.press_combination(['ctrl', '1'])  # 使用物品1
        """
        try:
            # 按顺序按下所有键
            for key in keys:
                keyboard.press(key)
            
            # 等待指定时长
            time.sleep(duration)
            
            # 按相反顺序释放所有键
            for key in reversed(keys):
                keyboard.release(key)
                
            self.logger.debug(f"执行组合键: {keys}, 持续时间: {duration}秒")
            return True
            
        except Exception as e:
            self.logger.error(f"组合键执行失败 {keys}: {e}")
            return False
            
    def move_mouse(self, x: int, y: int, duration: float = 0.2):
        """
        移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动时长(秒)
        """
        try:
            # 使用win32api移动鼠标
            win32api.SetCursorPos((x, y))
            if duration > 0:
                time.sleep(duration)
            self.logger.debug(f"移动鼠标到: ({x}, {y}), 持续时间: {duration}秒")
        except Exception as e:
            self.logger.error(f"鼠标移动失败 ({x}, {y}): {e}")
            
    def click_mouse(self, 
                   x: Optional[int] = None, 
                   y: Optional[int] = None,
                   button: str = 'left',
                   clicks: int = 1,
                   interval: float = 0.1):
        """
        执行鼠标点击
        
        Args:
            x: 点击X坐标(可选)
            y: 点击Y坐标(可选)
            button: 鼠标按键('left'/'right'/'middle')
            clicks: 点击次数
            interval: 点击间隔(秒)
        """
        try:
            # 如果提供了坐标，先移动到指定位置
            if x is not None and y is not None:
                self.move_mouse(x, y)
                
            # 获取当前鼠标位置
            current_x, current_y = win32api.GetCursorPos()
            
            # 根据按键类型选择事件
            if button == 'left':
                down_event = win32con.MOUSEEVENTF_LEFTDOWN
                up_event = win32con.MOUSEEVENTF_LEFTUP
            elif button == 'right':
                down_event = win32con.MOUSEEVENTF_RIGHTDOWN
                up_event = win32con.MOUSEEVENTF_RIGHTUP
            else:
                down_event = win32con.MOUSEEVENTF_MIDDLEDOWN
                up_event = win32con.MOUSEEVENTF_MIDDLEUP
                
            # 执行点击
            for _ in range(clicks):
                # 按下
                win32api.mouse_event(down_event, current_x, current_y, 0, 0)
                time.sleep(0.1)  # 短暂延迟
                # 释放
                win32api.mouse_event(up_event, current_x, current_y, 0, 0)
                
                # 如果还有更多点击，等待间隔时间
                if _ < clicks - 1:
                    time.sleep(interval)
                    
            self.logger.debug(f"点击鼠标 {button} 在 ({current_x}, {current_y}), {clicks}次")
            
        except Exception as e:
            self.logger.error(f"鼠标点击失败: {e}")

    # 12. **************测试 后期删除  执行动作序列  
    def execute_action_sequence(self, actions: List[Dict]):
        """
        执行动作序列
        
        Args:
            actions: 动作序列列表，每个动作是一个字典，包含:
                - type: 动作类型('key'/'mouse_move'/'mouse_click')
                - params: 动作参数字典
        """
        for action in actions:
            try:
                action_type = action.get('type')
                params = action.get('params', {})
                
                if action_type == 'key':
                    if isinstance(params.get('key'), list):
                        self.press_combination(keys=params['key'], duration=params.get('duration', 0.1))
                    else:
                        self.press_key(**params)
                elif action_type == 'mouse_move':
                    self.move_mouse(**params)
                elif action_type == 'mouse_click':
                    self.click_mouse(**params)
                else:
                    self.logger.warning(f"未知的动作类型: {action_type}")
                    
                # 执行动作后的延迟
                if 'delay' in action:
                    time.sleep(action['delay'])
                    
            except Exception as e:
                self.logger.error(f"动作序列执行失败: {e}")
                break 

    # 11. **************测试 后期删除 执行动作  
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
                    self.press_combination(**params)
                else:
                    # 单个按键操作,直接调用按键执行方法
                    # 例如: 'enter' 表示回车键
                    self.press_key(**params)
                    
            elif action_type == 'mouse_move':  # 鼠标移动操作
                # 移动鼠标到指定坐标
                # params需包含: x, y 坐标值
                self.move_mouse(**params)
                
            elif action_type == 'mouse_click':  # 鼠标点击操作
                # 在指定位置点击鼠标
                # params可包含: x, y 坐标, button 按键类型, clicks 点击次数
                self.click_mouse(**params)
                
            else:
                # 未知的动作类型,记录警告日志
                self.logger.warning(f"未知的动作类型: {action_type}")
                
        except Exception as e:
            # 动作执行出现异常时记录错误日志
            self.logger.error(f"动作执行失败: {e}")

    # 12.  **************测试 后期删除  执行动作序列  
    def execute_actions(self, actions: List[Dict]):
        """
        执行动作序列
        
        Args:
            actions: 动作序列列表
        """
        self.execute_action_sequence(actions)            

    def execute_move(self, direction: str):
        """
        执行移动动作
        
        Args:
            direction: 移动方向('上'/'右上'/'右'/'右下'/'下'/'左下'/'左'/'左上')
        
        Returns:
            bool: 执行是否成功
        """
        try:
            if direction in self.direction_angles:
                angle = self.direction_angles[direction]
                # 计算目标点坐标
                radian = math.radians(angle)
                target_x = int(self.center_point[0] + self.move_radius * math.cos(radian))
                target_y = int(self.center_point[1] - self.move_radius * math.sin(radian))
                
                # 确保坐标在游戏窗口范围内
                target_x = max(0, min(target_x, self.control_range[0]))
                target_y = max(0, min(target_y, self.control_range[1]))
                
                # 先移动鼠标到目标位置
                self.move_mouse(target_x, target_y)
                time.sleep(0.05)  # 短暂延迟确保鼠标到位
                
                # 使用click_mouse方法执行右键点击
                self.click_mouse(button='right')
                time.sleep(0.1)

                self.logger.debug(f"移动到方向: {direction}, 坐标: ({target_x}, {target_y})")
                return True
                
            self.logger.error(f"未知的移动方向: {direction}")
            return False
            
        except Exception as e:
            self.logger.error(f"移动执行失败: {e}")
            return False

    def execute_skill(self, skill_name: str):
        """执行技能"""
        if skill_name in self.skill_bindings:
            key = self.skill_bindings[skill_name]
            self.press_key(key)

    def execute_combo(self, combo_name: str):
        """执行连招"""
        if combo_name in self.action_config['combo_actions']:
            combo = self.action_config['combo_actions'][combo_name]
            for action in combo['sequence']:
                if action.get('action') == 'move':
                    self.execute_move(action['direction'])
                elif action.get('action') == 'skills':
                    self.execute_skill(action['key'])
                if 'delay' in action:
                    time.sleep(action['delay'])

    def _init_action_recording(self):
        """初始化动作记录"""
        record_config = self.action_config['action_recording']
        self.record_dir = Path(record_config['save_dir'])
        self.record_dir.mkdir(parents=True, exist_ok=True)
        
        self.record_format = record_config['format']
        self.record_interval = record_config['record_interval']
        
        # 使用双端队列存储最近的动作记录
        self.action_history = deque(maxlen=1000)  
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _init_action_space(self):
        """初始化动作空间"""
        rl_config = self.action_config['rl_config']
        
        # 构建离散动作空间
        self.discrete_actions = {}
        for action_group in rl_config['action_space']['discrete_actions']:
            self.discrete_actions[action_group['name']] = action_group['values']
            
        # 构建连续动作空间(如果需要)
        self.continuous_actions = {}
        if 'continuous_actions' in rl_config['action_space']:
            self.continuous_actions = rl_config['action_space']['continuous_actions']
    
    def record_action(self, 
                     action_type: str,
                     action_name: str,
                     params: Dict[str, Any],
                     result: bool,
                     game_state: Optional[Dict] = None):
        """
        记录执行的动作
        
        Args:
            action_type: 动作类型
            action_name: 动作名称
            params: 动作参数
            result: 执行结果
            game_state: 当前游戏状态(可选)
        """
        if not self.recording_enabled:
            return
            
        record = ActionExecutor.ActionRecord(
            timestamp=time.time(),
            action_type=action_type,
            action_name=action_name,
            params=params,
            result=result,
            game_state=game_state
        )
        
        self.action_history.append(record)
        self.logger.debug(f"记录动作: {action_type}-{action_name}")
        
    def save_action_history(self):
        """保存动作历史记录"""
        if not self.recording_enabled or not self.action_history:
            return
            
        filename = f"action_record_{self.current_session}.{self.record_format}"
        save_path = self.record_dir / filename
        
        try:
            records = [
                {
                    'timestamp': record.timestamp,
                    'action_type': record.action_type,
                    'action_name': record.action_name,
                    'params': record.params,
                    'result': record.result,
                    'game_state': record.game_state
                }
                for record in self.action_history
            ]
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"动作历史记录已保存: {save_path}")
            
        except Exception as e:
            self.logger.error(f"保存动作历史记录失败: {e}")
            
    def get_action_space(self) -> Dict:
        """
        获取动作空间定义(为强化学习准备)
        
        Returns:
            Dict: 包含离散和连续动作空间的定义
        """
        return {
            'discrete': self.discrete_actions,
            'continuous': self.continuous_actions
        }
  
    def execute_attack(self, target_type: str, mode: Optional[str] = None):
        """
        执行攻击动作
        
        Args:
            target_type: 目标类型 ('monster'/'player')
            mode: 控制模式 ('mouse_only'/'mouse_and_keyboard')，
                  如果不指定则使用默认模式
        """
        try:
            # 获取攻击配置
            attack_config = self.action_config['basic_actions']['attack']
            
            # 如果没有指定模式，使用默认模式
            if mode is None:
                mode = attack_config.get('default_mode', 'keyboard_mouse')
            
            # 获取目标类型的配置
            target_config = attack_config['modes'].get(target_type)
            if not target_config:
                self.logger.error(f"未知的目标类型: {target_type}")
                return False
            
            # 获取具体模式的配置
            mode_config = target_config.get(mode)
            if not mode_config:
                self.logger.error(f"未知的控制模式: {mode}")
                return False
            
            # 执行攻击
            if mode == 'mouse_only':
                # 纯鼠标模式
                current_x, current_y = win32api.GetCursorPos()
                for _ in range(mode_config['clicks']):
                    if mode_config['button'] == 'left':
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, current_x, current_y, 0, 0)
                        time.sleep(0.1)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, current_x, current_y, 0, 0)
                    else:
                        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, current_x, current_y, 0, 0)
                        time.sleep(0.1)
                        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, current_x, current_y, 0, 0)
            else:
                # 键鼠组合模式
                modifier_key = mode_config['modifier_key']
                keyboard.press(modifier_key)
                current_x, current_y = win32api.GetCursorPos()
                for _ in range(mode_config['clicks']):
                    if mode_config['button'] == 'left':
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, current_x, current_y, 0, 0)
                        time.sleep(0.1)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, current_x, current_y, 0, 0)
                    else:
                        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, current_x, current_y, 0, 0)
                        time.sleep(0.1)
                        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, current_x, current_y, 0, 0)
                keyboard.release(modifier_key)
            
            self.logger.debug(f"执行攻击: {target_type} - {mode}")
            return True
            
        except Exception as e:
            self.logger.error(f"攻击执行失败: {e}")
            return False

    def attack_monster(self, mode: Optional[str] = None):
        """攻击怪物的快捷方法"""

        return self.execute_attack('monster', mode)
    
    def attack_player(self, mode: Optional[str] = None):
        """攻击玩家的快捷方法"""
        return self.execute_attack('player', mode)

    def execute_other_skill(self, skill_name: str):
        """
        执行其他技能
        
        Args:
            skill_name: 技能名称('战斗'/'打坐'/'招呼')
        
        Returns:
            bool: 执行是否成功
        """
        try:
            if skill_name in self.action_config['basic_actions']['other_skills']['bindings']:
                key = self.action_config['basic_actions']['other_skills']['bindings'][skill_name]
                self.press_key(key)
                return True
            return False
        except Exception as e:
            self.logger.error(f"其他技能执行失败: {e}")
            return False

    def use_item(self, item_id: str):
        """
        使用物品
        
        Args:
            item_id: 物品ID('item_1' to 'item_6')
        
        Returns:
            bool: 执行是否成功
        
        示例:
            >>> action_executor.use_item('item_1')  # 使用小药水(Ctrl+1)
        """
        try:
            if item_id in self.action_config['basic_actions']['items']['bindings']:
                keys = self.action_config['basic_actions']['items']['bindings'][item_id]
                self.press_combination(keys)
                return True
            return False
        except Exception as e:
            self.logger.error(f"物品使用失败: {e}")
            return False

    # === 目标选择方法 ===
    def select_target(self, 
                     selection_type: str = None,
                     x: Optional[int] = None,
                     y: Optional[int] = None,
                     mode: str = None):
        """
        目标选择方法
        
        Args:
            selection_type: 键盘模式下的选择类型
                - 'next': 下一个目标
                - 'previous': 上一个目标
                - 'nearest': 最近目标
                - 'cancel': 取消选择
            x: 鼠标模式下的目标X坐标
            y: 鼠标模式下的目标Y坐标
            mode: 选择模式('keyboard'/'mouse')，不指定则使用默认模式
                
        Returns:
            bool: 是否成功
            
        示例:
            # 键盘模式
            >>> action_executor.select_target(selection_type='next')  # Tab键选择下一个
            >>> action_executor.select_target(selection_type='nearest')  # ~键选择最近
            
            # 鼠标模式
            >>> action_executor.select_target(x=500, y=300)  # 点击指定坐标选择目标
        """
        try:
            target_config = self.action_config['basic_actions']['target_selection']
            
            # 如果没有指定模式，使用配置文件中的默认模式
            mode = mode or target_config.get('default_mode', 'mouse')
            target_type = target_config.get('type', 'mouse')
            
            # 鼠标模式
            if mode == 'mouse':
                if x is not None and y is not None:
                    mouse_config = target_config['mouse']
                    self.click_mouse(
                        x=x,
                        y=y,
                        button=mouse_config['button'],
                        clicks=mouse_config['clicks']
                    )
                    return True
                else:
                    self.logger.error("鼠标模式需要提供坐标")
                    return False
                
            # 键盘模式
            elif mode == 'keyboard':
                if selection_type:
                    keyboard_config = target_config['keyboard']['bindings']
                    if selection_type == 'next' and 'next_target' in keyboard_config:
                        self.press_key(keyboard_config['next_target'])
                        return True
                    elif selection_type == 'previous' and 'previous_target' in keyboard_config:
                        self.press_combination(keyboard_config['previous_target'])
                        return True
                    elif selection_type == 'nearest' and 'nearest_target' in keyboard_config:
                        self.press_key(keyboard_config['nearest_target'])
                        return True
                    elif selection_type == 'cancel' and 'cancel_target' in keyboard_config:
                        self.press_key(keyboard_config['cancel_target'])
                        return True
                    
                self.logger.error(f"键盘模式需要提供选择类型")
                return False
            
            else:
                self.logger.error(f"未知的选择模式: {mode}")
                return False
            
        except Exception as e:
            self.logger.error(f"目标选择失败: {e}")
            return False

    def select_special_target(self, target_type: str):
        """
        特殊目标选择方法
        
        Args:
            target_type: 目标类型
                - 'nearest_monster': 最近的怪物
                - 'nearest_player': 最近的玩家
                - 'nearest_npc': 最近的NPC
                - 'nearest_item': 最近的物品
                
        Returns:
            bool: 是否成功
            
        示例:
            >>> action_executor.select_special_target('nearest_monster')  # 选择最近的怪物
            >>> action_executor.select_special_target('nearest_npc')  # 选择最近的NPC
        """
        try:
            special_targets = self.action_config['basic_actions']['target_selection']['special_targets']
            
            if target_type in special_targets:
                self.press_key(special_targets[target_type])
                return True
            
            self.logger.error(f"未知的特殊目标类型: {target_type}")
            return False
            
        except Exception as e:
            self.logger.error(f"特殊目标选择失败: {e}")
            return False

    # === UI交互方法 ===
    def open_ui(self, ui_type: str):
        """
        打开UI界面
        
        Args:
            ui_type: UI类型
                - 'menu': 菜单
                - 'character': 角色
                - 'inventory': 背包
                - 'skills': 技能
                - 'other_skills': 其他技能
                - 'guild': 公会
                - 'mission': 任务
                - 'shop': 商城
                - 'assistant': 辅助
                - 'map': 地图
                
        Returns:
            bool: 是否成功
            
        示例:
            >>> action_executor.open_ui('character')  # 打开角色界面
            >>> action_executor.open_ui('inventory')  # 打开背包
        """
        try:
            if ui_type in self.action_config['ui_actions']:
                ui_config = self.action_config['ui_actions'][ui_type]
                if isinstance(ui_config['key'], list):
                    self.press_combination(ui_config['key'])
                else:
                    self.press_key(ui_config['key'])
                self.logger.debug(f"打开UI界面: {ui_type}")
                return True
                
            self.logger.error(f"未知的UI类型: {ui_type}")
            return False
            
        except Exception as e:
            self.logger.error(f"打开UI界面失败: {e}")
            return False


if __name__ == "__main__":
    # 配置文件路径
    basic_config_path = "F:/2025Projects/1000Y/config/env/status_collection_config.yaml"
    action_config_path = "config/env/action_config.yaml"
    
    # 初始化配置管理器
    config_manager = ConfigManager(basic_config_path, action_config_path)
    
    # 获取日志配置
    logger_config = config_manager.get_logger_config()
    
    # 初始化日志
    logger = LoggerManager(
        name='Main',
        **logger_config
    ).get_logger()

    # 创建动作执行器实例
    action_executor = ActionExecutor(
        logger=logger,  
        config_manager=config_manager
    )
    
    # 添加10秒倒计时
    print("程序将在10秒后开始执行，请切换到游戏窗口...")
    for i in range(10, 0, -1):
        print(f"倒计时: {i}秒")
        time.sleep(1)
    print("开始执行!")

    try:
        # 测试目标选择
        action_executor.select_target(mode='keyboard', selection_type='nearest')
        time.sleep(1)
        
        # 测试攻击
        action_executor.attack_monster(mode='keyboard_mouse')
        time.sleep(1)
        
    finally:
        action_executor.save_action_history()