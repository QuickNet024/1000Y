from pynput import keyboard, mouse
from typing import Set, Dict, Tuple, Optional
import logging
import json
from datetime import datetime
import time
from pathlib import Path

class InputListener:
    def __init__(self, 
                 keys_to_monitor: Set[str],
                 mouse_area: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
                 keyboard_log: str = "data/raw/actions/keyboard_actions.json",
                 mouse_log: str = "data/raw/actions/mouse_actions.json",
                 show_events: bool = True):
        
        self.keys_to_monitor = {k.lower() for k in keys_to_monitor}
        self.mouse_area = mouse_area
        self.keyboard_log = keyboard_log
        self.mouse_log = mouse_log
        
        # 确保日志文件目录存在
        for file_path in [keyboard_log, mouse_log]:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
        # 创建或清空日志文件
        for file_path in [keyboard_log, mouse_log]:
            with open(file_path, 'w', encoding='utf-8') as f:
                pass
        
        # 键盘状态跟踪
        self.key_states = {}  # 记录按键的按下时间和状态
        
        # 鼠标状态跟踪
        self.mouse_states = {
            'left': {'press_time': 0, 'last_click_time': 0, 'last_click_pos': None},
            'right': {'press_time': 0, 'last_click_time': 0, 'last_click_pos': None},
            'middle': {'press_time': 0, 'last_click_time': 0, 'last_click_pos': None}
        }
        
        # 配置参数
        self.double_click_time = 0.3
        self.long_press_time = 0.5
        
        # 特殊键映射
        self.special_keys = {
            keyboard.Key.shift: 'shift',
            keyboard.Key.shift_l: 'shift',
            keyboard.Key.shift_r: 'shift',
            keyboard.Key.ctrl: 'ctrl',
            keyboard.Key.ctrl_l: 'ctrl',
            keyboard.Key.ctrl_r: 'ctrl',
            keyboard.Key.alt: 'alt',
            keyboard.Key.alt_l: 'alt',
            keyboard.Key.alt_r: 'alt',
            keyboard.Key.tab: 'tab',
            keyboard.Key.f5: 'f5',
            keyboard.Key.f6: 'f6',
            keyboard.Key.f7: 'f7',
            keyboard.Key.f8: 'f8',
            keyboard.Key.f9: 'f9',
            keyboard.Key.f10: 'f10',
            keyboard.Key.f11: 'f11',
            keyboard.Key.f12: 'f12',
            keyboard.Key.space: 'space'
        }
        
        # 初始化监听器
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
            suppress=False
        )
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
            suppress=False
        )
        
        # 获取logger
        self.logger = logging.getLogger(__name__)
        
        # 用于实时状态显示
        self.current_mouse_event = None
        self.current_keyboard_event = None
        
        self.show_events = show_events  # 是否显示输入事件
    
    def _get_key_name(self, key) -> Optional[str]:
        """获取标准化的按键名称"""
        try:
            return key.char.lower()
        except AttributeError:
            return self.special_keys.get(key)
    
    def _log_event(self, event_data: dict, is_mouse: bool = False):
        """记录事件到日志文件"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                **event_data
            }
            
            log_file = self.mouse_log if is_mouse else self.keyboard_log
            
            # 保存用于实时显示
            if is_mouse:
                self.current_mouse_event = log_entry
            else:
                self.current_keyboard_event = log_entry
                
            # 写入文件
            with open(log_file, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')
                
            # 根据配置决定是否显示事件信息
            if self.show_events:
                if is_mouse:
                    if 'scroll' in event_data.get('key', ''):
                        self.logger.debug(f"鼠标事件: {event_data['key']} - 位置: ({event_data['x']}, {event_data['y']})")
                    else:
                        self.logger.debug(f"鼠标事件: {event_data['key']} - 位置: ({event_data['x']}, {event_data['y']}) - 持续: {event_data.get('duration', 0):.2f}秒")
                else:
                    self.logger.debug(f"键盘事件: {event_data['key']} - 持续: {event_data.get('duration', 0):.2f}秒")
                
        except Exception as e:
            self.logger.error(f"写入事件日志失败: {str(e)}")
            raise
    
    def _on_key_press(self, key):
        """键盘按下事件处理"""
        key_name = self._get_key_name(key)
        if not key_name or key_name not in self.keys_to_monitor:
            return
            
        # 只记录首次按下
        if key_name not in self.key_states:
            self.key_states[key_name] = {'press_time': time.time()}
    
    def _on_key_release(self, key):
        """键盘释放事件处理"""
        key_name = self._get_key_name(key)
        if not key_name or key_name not in self.keys_to_monitor:
            return
            
        key_state = self.key_states.pop(key_name, None)
        if key_state:
            duration = time.time() - key_state['press_time']
            self._log_event({
                'type': 'Keyboard',
                'key': key_name,
                'duration': round(duration, 3)
            })
    
    def _on_mouse_click(self, x, y, button, pressed):
        """鼠标点击事件处理"""
        if not self._is_in_area(x, y):
            return
            
        # 扩展按键映射
        button_name = {
            mouse.Button.left: 'left',
            mouse.Button.right: 'right',
            mouse.Button.middle: 'middle'
        }.get(button)
        
        if not button_name:
            return
            
        current_time = time.time()
        state = self.mouse_states[button_name]
        
        if pressed:
            state['press_time'] = current_time
        else:
            duration = current_time - state['press_time']
            
            # 判断事件类型
            if duration >= self.long_press_time:
                action_key = f'mouse_long_{button_name}_click'
            elif (current_time - state['last_click_time'] < self.double_click_time and 
                  state['last_click_pos'] == (x, y)):
                action_key = f'mouse_double_{button_name}_click'
            else:
                action_key = f'mouse_{button_name}'
            
            # 记录事件
            self._log_event({
                'type': 'Mouse',
                'key': action_key,
                'x': x,
                'y': y,
                'duration': round(duration, 3)
            }, is_mouse=True)
            
            # 更新最后一次点击信息
            state['last_click_time'] = current_time
            state['last_click_pos'] = (x, y)
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """鼠标滚轮事件处理"""
        if not self._is_in_area(x, y):
            return
        
        # 判断滚动方向
        if dy > 0:
            action_key = 'mouse_scroll_up'
        elif dy < 0:
            action_key = 'mouse_scroll_down'
        elif dx > 0:
            action_key = 'mouse_scroll_right'
        elif dx < 0:
            action_key = 'mouse_scroll_left'
        else:
            return
        
        # 记录滚轮事件
        self._log_event({
            'type': 'Mouse',
            'key': action_key,
            'x': x,
            'y': y,
            'scroll_dx': dx,
            'scroll_dy': dy
        }, is_mouse=True)
    
    def _is_in_area(self, x: int, y: int) -> bool:
        """检查坐标是否在监听区域内"""
        if not self.mouse_area:
            return True
        (x1, y1), (x2, y2) = self.mouse_area
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def get_current_state(self) -> dict:
        """获取当前输入状态"""
        return {
            'keys_pressed': list(self.key_states.keys()),
            'mouse_event': self.current_mouse_event,
            'keyboard_event': self.current_keyboard_event
        }
    
    def start(self):
        """开始监听"""
        try:
            self.keyboard_listener.start()
            self.mouse_listener.start()
            
            # 等待监听器完全启动
            if not self.keyboard_listener.is_alive() or not self.mouse_listener.is_alive():
                raise RuntimeError("监听器启动失败")
                
            return True
        except Exception as e:
            self.logger.error(f"启动监听器失败: {str(e)}")
            return False
    
    def stop(self):
        """停止监听"""
        try:
            if self.keyboard_listener.is_alive():
                self.keyboard_listener.stop()
            if self.mouse_listener.is_alive():
                self.mouse_listener.stop()
            
            # 等待监听器完全停止
            self.keyboard_listener.join()
            self.mouse_listener.join()
            return True
        except Exception as e:
            self.logger.error(f"停止监听器失败: {str(e)}")
            return False 