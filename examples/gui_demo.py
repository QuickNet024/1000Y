import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from screen_split_demo import GameScreenProcessor, ConfigManager, LoggerManager
from src.gui.game_monitor_gui import GameMonitorGUI

def main():
    """GUI版本主函数"""
    # 配置文件路径
    project_root = Path(__file__).parent.parent
    basic_config_path = project_root / "config/env/status_collection_config.yaml"

    # 使用配置管理器获取日志配置
    config_manager = ConfigManager(basic_config_path)
    logger_config = config_manager.get_logger_config()
    
    # 初始化主程序日志
    logger = LoggerManager(
        name='Main',
        **logger_config
    ).get_logger()

    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 创建处理器
    processor = GameScreenProcessor(
        config_manager=config_manager,
        logger=logger
    )
    
    # 创建并显示GUI
    gui = GameMonitorGUI(processor)
    gui.show()
    
    # 启动事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 