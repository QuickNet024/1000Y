import logging
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

class LoggerManager:
    """日志管理类"""
    
    # 类变量
    _shared_log_file = None
    _last_hour = None
    _loggers = {}  # 用于存储所有创建的logger实例
    _debug_mode = False  # 关闭调试模式
    
    def __init__(self, name: str = None, **logger_config):
        """初始化日志管理器
        
        Args:
            name: 日志器名称，如果不提供则使用调用类的名称
            **logger_config: 日志配置参数
        """
        # 如果没有提供name，获取调用者的类名
        if name is None:
            import inspect
            # 获取调用栈中的第一个非LoggerManager的类
            for frame_info in inspect.stack()[1:]:
                frame = frame_info.frame
                if 'self' in frame.f_locals:
                    caller = frame.f_locals['self']
                    if not isinstance(caller, LoggerManager):
                        name = caller.__class__.__name__
                        break
            
            # 如果还是没有找到名称，使用默认值
            if name is None:
                name = 'UnknownModule'
        
        self.name = name
        self.log_dir = Path(logger_config.get('log_dir', 'logs'))
        self.log_level = logger_config.get('log_level', 'INFO')
        self.console_log_level = logger_config.get('console_log_level', 'INFO')
        self.file_log_level = logger_config.get('file_log_level', 'DEBUG')
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建格式器
        self.formatter = logging.Formatter(
            '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 检查是否已经存在该名称的logger
        if name in LoggerManager._loggers:
            if self._debug_mode:
                print(f"Reusing existing logger: {name}")
            self.logger = LoggerManager._loggers[name]
        else:
            if self._debug_mode:
                print(f"Creating new logger: {name}")
            # 创建新的logger
            self.logger = logging.getLogger(name)
            self.logger.setLevel(getattr(logging, self.log_level.upper()))
            self.logger.propagate = logger_config.get('propagate', False)
            
            # 清除已有的处理器
            if self.logger.handlers:
                if self._debug_mode:
                    print(f"Clearing existing handlers for {name}")
                self.logger.handlers.clear()
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.console_log_level.upper()))
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)
            
            # 保存logger实例
            LoggerManager._loggers[name] = self.logger
        
        # 确保创建或更新文件处理器
        self._ensure_file_handler()
        
        if self._debug_mode:
            print(f"Current handlers for {name}:")
            for handler in self.logger.handlers:
                print(f"- {type(handler).__name__}")
            print("=== Init Complete ===\n")
    
    def _ensure_file_handler(self):
        """确保创建文件处理器"""
        if self._debug_mode:
            print(f"\n=== Ensuring File Handler ===")
            print(f"Logger: {self.name}")
        
        current_time = datetime.now()
        current_hour = current_time.strftime('%Y%m%d_%H')
        current_timestamp = current_time.strftime('%Y%m%d_%H%M%S')
        
        # 如果没有文件处理器或者到了新的小时，创建新的文件处理器
        if LoggerManager._shared_log_file is None or LoggerManager._last_hour != current_hour:
            if self._debug_mode:
                print(f"Creating new log file")
                print(f"Last hour: {LoggerManager._last_hour}")
                print(f"Current hour: {current_hour}")
            
            # 创建新的日志文件
            LoggerManager._last_hour = current_hour
            LoggerManager._shared_log_file = self.log_dir / f"game_collect_{current_timestamp}.log"
        
        # 确保当前 logger 有文件处理器
        has_file_handler = any(isinstance(handler, logging.FileHandler) 
                              for handler in self.logger.handlers)
        
        if not has_file_handler:
            if self._debug_mode:
                print(f"Adding file handler to {self.name}")
                print(f"Before: {[type(h).__name__ for h in self.logger.handlers]}")
            
            # 创建新的文件处理器
            file_handler = logging.FileHandler(LoggerManager._shared_log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, self.file_log_level.upper()))
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
            
            if self._debug_mode:
                print(f"After: {[type(h).__name__ for h in self.logger.handlers]}")
    
    def get_logger(self) -> logging.Logger:
        """获取logger实例"""
        self._ensure_file_handler()  # 确保有文件处理器
        
        # 如果是从类实例调用，使用类的 MODULE_NAME
        if hasattr(self, 'MODULE_NAME'):
            self.name = self.MODULE_NAME
        # 如果已经设置了name，就使用设置的name
        elif not self.name:
            self.name = 'UnknownModule'
        
        # 检查是否已经存在该名称的logger
        if self.name in LoggerManager._loggers:
            return LoggerManager._loggers[self.name]
        
        # 创建新的logger
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level.upper()))
        logger.propagate = False
        
        # 清除已有的处理器
        if logger.handlers:
            logger.handlers.clear()
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.console_log_level.upper()))
        console_handler.setFormatter(self.formatter)
        logger.addHandler(console_handler)
        
        # 保存logger实例
        LoggerManager._loggers[self.name] = logger
        
        return logger
    
    @classmethod
    def get_log_file(cls) -> Optional[Path]:
        """获取当前共享的日志文件路径"""
        return cls._shared_log_file
    
    @staticmethod
    def setup_module_logger(module_name: str,
                          log_dir: Union[str, Path],
                          log_level: str = "INFO") -> logging.Logger:
        """设置模块级别的logger
        
        Args:
            module_name: 模块名称
            log_dir: 日志目录
            log_level: 日志级别
            
        Returns:
            logging.Logger: 配置好的logger实例
        """
        logger_manager = LoggerManager(
            name=module_name,
            log_dir=log_dir,
            log_level=log_level
        )
        return logger_manager.get_logger() 