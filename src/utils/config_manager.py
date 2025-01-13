import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: Path):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.basic_config = self.config.get('basic_config')
        self.area_config = {
            key: value for key, value in self.config.items()
            if key != 'basic_config'
        }
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")
        
    def get_logger_config(self) -> Dict[str, Any]:
        """获取日志配置
        
        Returns:
            日志配置字典
        """
        basic_config = self.basic_config
        return {
            'log_dir': Path(basic_config.get('base_output_dir')) / basic_config.get('log_dir', "logs"),
            'log_level': basic_config.get('log_level', "INFO"),
            'console_log_level': basic_config.get('console_log_level', "INFO"),
            'file_log_level': basic_config.get('file_log_level', "DEBUG")
        }
    # 

