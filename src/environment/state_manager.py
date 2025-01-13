import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

class StateManager:
    """状态管理类"""
    MODULE_NAME = 'StateManager'
    
    def __init__(self, basic_config: dict, area_config: dict, logger: logging.Logger):
        """
        初始化状态管理器
        
        Args:
            state_dir: 状态文件保存目录
        """
        self.logger = logger
        self.logger.info("<<<<<<<<<<<<<<<<<<状态管理器初始化开始...>>>>>>>>>>>>>>>>>>")

        self.basic_config = basic_config
        self.area_config = area_config
        self.base_output_dir = Path(basic_config.get('base_output_dir', 'output'))
        self.state_dir = self.base_output_dir / basic_config.get('state_dir', 'states_json')
        self.current_state = {}

        self.logger.info("=========================状态管理器初始化完成=========================")
        
    def update(self, new_state: Dict[str, Any], timestamp: str = None):
        """
        更新状态
        
        Args:
            new_state: 新的状态数据
            timestamp: 时间戳，用于文件命名
        """
        # 更新当前状态
        self.current_state.update(new_state)
        
        # 添加时间戳
        self.current_state['timestamp'] = timestamp or str(time.time()).replace('.', '_')


        # 保存状态到文件
        self._save_state(timestamp)
        
    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.current_state
        
    def _save_state(self, timestamp: str = None):
        """
        保存状态到文件
        
        Args:
            timestamp: 时间戳，用于文件命名
        """
        if timestamp:
            state_file = self.state_dir / f"{timestamp}.json"

        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态文件失败: {str(e)}")
