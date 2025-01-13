import yaml
from pathlib import Path
from typing import Union, Dict, Any

class ConfigParser:
    """配置文件解析类"""
    
    @staticmethod
    def parse_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """解析YAML配置文件
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            Dict: 解析后的配置字典
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"找不到配置文件: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) 