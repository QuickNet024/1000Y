import sys
from pathlib import Path
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from src.data.collector import DataCollector, ConfigManager, LoggerManager
# from screen_split_demo import GameScreenProcessor, ConfigManager, LoggerManager
from src.gui.game_monitor_gui import GameMonitorGUI

def main():
    """GUI版本主函数"""
    # 配置文件路径
    basic_config_path = project_root / "config/env/status_collection_config.yaml"

    # 使用配置管理器获取日志配置
    config_manager = ConfigManager(basic_config_path)
    logger_config = config_manager.get_logger_config()
    
    # 初始化主程序日志
    logger = LoggerManager(
        name='Main',
        **logger_config
    ).get_logger()

    # 添加环境检查
    logger.debug(f"当前工作目录: {os.getcwd()}")
    logger.debug(f"Python路径: {sys.path}")
    logger.debug(f"环境变量: {dict(os.environ)}")

    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 创建处理器
    try:
        processor = DataCollector(
            config_manager=config_manager,
            logger=logger
        )
        logger.debug("处理器初始化成功")
    except Exception as e:
        logger.error(f"处理器初始化失败: {e}", exc_info=True)
        return
        
    # 创建并显示GUI
    try:
        gui = GameMonitorGUI(processor)
        gui.show()
        logger.debug("GUI初始化成功")
    except Exception as e:
        logger.error(f"GUI初始化失败: {e}", exc_info=True)
        return
    
    # 启动事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 