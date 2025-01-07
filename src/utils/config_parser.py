import yaml
from pathlib import Path

class ConfigParser:
    """配置文件解析类"""
    
    @staticmethod
    def parse(config_path):
        """解析yaml配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            dict: 配置字典
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        return config 