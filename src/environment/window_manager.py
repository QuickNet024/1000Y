# src/environment/window_manager.py
import win32gui
import win32con
import win32com.client
import time
import win32api
import win32process
from pathlib import Path
import logging

class WindowManager:
    """窗口管理类
    
    用于管理游戏窗口的查找、激活、移动等操作。
    主要功能：
    1. 根据窗口标题查找目标窗口
    2. 获取和设置窗口位置
    3. 激活窗口并置于前台
    4. 监控窗口状态
    """
    
    MODULE_NAME = 'WindowManager'
    
    def __init__(self, basic_config: dict, logger: logging.Logger = None):
        """初始化窗口管理器"""
        if logger is None:
            from src.utils.logger_manager import LoggerManager
            self.logger = LoggerManager().get_logger()  # 自动使用 WindowManager 作为名称
        else:
            self.logger = logger
        self.logger.info(f"<<<<<<<<<<<<<<<<<<{self.MODULE_NAME}初始化开始>>>>>>>>>>>>>>>>>>")
        self.basic_config = basic_config
        # 从配置中获取窗口标题
        self.window_title = self.basic_config.get('window_name', '')
        if not self.window_title:
            raise ValueError("游戏窗口标题未配置")
        self.logger.debug(f"目标窗口标题: {self.window_title}")
        
        # 找到窗口句柄
        self.hwnd = self._find_window_by_title(self.window_title)
        if self.hwnd:
            self.logger.debug(f"成功找到窗口 '{self.window_title}' (句柄: {self.hwnd})")
            
            # 获取窗口位置和大小
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            width = right - left
            height = bottom - top
            self.logger.debug(f"窗口位置: ({left}, {top}), 大小: {width}x{height}")
            
            # 尝试激活窗口
            self.activate_window()
            
        self.logger.info("=========================窗口管理器初始化完成=========================")
        
    def _find_window_by_title(self, title):
        """根据窗口标题模糊查找窗口句柄
        
        支持模糊匹配，不区分大小写。如果找到多个匹配窗口，返回第一个。
        
        Args:
            title: 要查找的窗口标题
            
        Returns:
            int: 窗口句柄
            
        Raises:
            Exception: 当找不到匹配的窗口时
        """
        def callback(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_title and title.lower() in window_title.lower():
                    ctx['hwnd'] = hwnd
                    ctx['title'] = window_title
                    self.window_title = window_title
                    self.logger.debug(f"找到匹配窗口: {window_title}")
        
        # 获取所有可见窗口中匹配的窗口
        context = {'hwnd': 0, 'title': ''}
        win32gui.EnumWindows(callback, context)
        
        if context['hwnd'] == 0:
            self.logger.debug("当前所有窗口:")
            def print_window(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    self.logger.debug(win32gui.GetWindowText(hwnd))
            win32gui.EnumWindows(print_window, None)
            raise Exception(f"未找到标题包含 '{title}' 的窗口")
            
        return context['hwnd']
    
    def get_window_size(self):
        """获取窗口的当前大小
        
        Returns:
            tuple: (width, height) 窗口的宽度和高度
            
        Raises:
            Exception: 当窗口句柄无效时
        """
        if self.hwnd is None:
            raise Exception("未找到有效的窗口句柄")
        
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        width = right - left
        height = bottom - top
        return width, height
    
    def move_window(self, x, y):
        """将窗口移动到指定位置
        
        保持窗口大小不变，只改变位置。
        
        Args:
            x: 目标x坐标
            y: 目标y坐标
            
        Raises:
            Exception: 当窗口句柄无效或移动失败时
        """
        if self.hwnd is None:
            raise Exception("未找到有效的窗口句柄")
        
        try:
            # 获取当前窗口大小
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            width = right - left
            height = bottom - top
            
            # 直接移动窗口
            win32gui.MoveWindow(self.hwnd, x, y, width, height, True)
            self.logger.debug(f"窗口已移动到 ({x}, {y})")
            
        except Exception as e:
            self.logger.error(f"移动窗口失败: {e}")

    def get_window_position(self):
        """获取窗口的当前位置
        
        Returns:
            tuple: (left, top) 窗口左上角的坐标
            
        Raises:
            Exception: 当窗口句柄无效时
        """
        if self.hwnd is None:
            raise Exception("未找到有效的窗口句柄")
        
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        return left, top
    
    def activate_window(self):
        """激活窗口并将其置于前台
        
        尝试多种方法激活窗口：
        1. 恢复最小化的窗口
        2. 显示窗口
        3. 强制激活窗口
        
        Returns:
            bool: 激活是否成功
        """
        try:
            # 检查窗口是否存在
            if not win32gui.IsWindow(self.hwnd):
                self.logger.error(f"窗口句柄 {self.hwnd} 无效")
                return False
                
            # 如果窗口最小化，恢复它
            if win32gui.IsIconic(self.hwnd):
                self.logger.debug("窗口已最小化，正在恢复...")
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)  # 给系统更多时间来恢复窗口
            
            # 确保窗口可见
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            
            # 强制激活窗口
            self.force_activate_window()
            
            # 验证窗口是否真的被激活
            active_hwnd = win32gui.GetForegroundWindow()
            if active_hwnd == self.hwnd:
                self.logger.debug("窗口已成功激活")
                return True
            else:
                self.logger.error(f"窗口激活失败，当前活动窗口: {win32gui.GetWindowText(active_hwnd)}")
                return False
                
        except Exception as e:
            self.logger.error(f"激活窗口时发生错误: {e}")
            return False

    def force_activate_window(self):
        """使用多种方法强制激活窗口
        
        依次尝试三种方法：
        1. SetForegroundWindow
        2. 模拟Alt键
        3. AttachThreadInput
        
        每种方法失败后会尝试下一种方法。
        """
        try:
            # 方法1: 使用SetForegroundWindow
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.1)
            
            # 如果方法1失败，尝试方法2
            if win32gui.GetForegroundWindow() != self.hwnd:
                # 方法2: 模拟Alt键
                shell = win32com.client.Dispatch("WScript.Shell")
                shell.SendKeys('%')
                time.sleep(0.1)
                win32gui.SetForegroundWindow(self.hwnd)
                
            # 如果还是失败，尝试方法3
            if win32gui.GetForegroundWindow() != self.hwnd:
                # 方法3: 使用AttachThreadInput
                current_thread = win32api.GetCurrentThreadId()
                fore_thread = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]
                win32process.AttachThreadInput(current_thread, fore_thread, True)
                win32gui.SetForegroundWindow(self.hwnd)
                win32gui.BringWindowToTop(self.hwnd)
                win32process.AttachThreadInput(current_thread, fore_thread, False)
                
        except Exception as e:
            self.logger.error(f"强制激活窗口失败: {e}")

