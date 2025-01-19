import sys
import os
import time
from pathlib import Path
import logging

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.config_manager import ConfigManager
from src.utils.logger_manager import LoggerManager
from src.environment.input_control import InputMonitor

def main():
    """测试输入监控功能"""
    MODULE_NAME = 'Main'  # 主程序的模块名
    try:
        # 配置文件路径
        basic_config_path = "config/env/status_collection_config.yaml"
        action_config_path = "config/env/action_config.yaml"
        
        # 初始化配置管理器
        config_manager = ConfigManager(basic_config_path, action_config_path)
        
        # 初始化主程序日志
        logger_config = config_manager.get_logger_config()
        logger = LoggerManager(
            name=MODULE_NAME,  # 使用主程序的模块名
            **logger_config
        ).get_logger()
        
        # 创建输入监控器
        input_monitor = InputMonitor(
            action_config=config_manager.action_config,
            save_dir="B:/1000Y_DATA_TEMP/data/input_records",
            logger=LoggerManager(name='InputMonitor', **logger_config).get_logger()
        )
    except Exception as e:
        print(f"初始化失败: {e}")
        return
    
    print("测试将在5秒后开始，请准备...")
    for i in range(5, 0, -1):
        print(f"倒计时: {i}秒")
        time.sleep(1)
    print("开始记录输入!")
    
    try:
        # 开始监听
        input_monitor.start()
        
        # 等待60秒进行测试
        print("请在60秒内进行测试操作...")
        print("支持的操作:")
        print("1. 技能按键 (F2-F12)")
        print("2. 物品使用 (Ctrl + 1-6)")
        print("3. UI操作 (Alt + 1-8, Alt + M)")
        print("4. 移动操作 (右键点击，相对于屏幕中心点计算方向)")
        print("5. 攻击操作 (左键点击或Shift+左键)")
        print("\n按Ctrl+C结束测试")
        
        time.sleep(20)
        
    except KeyboardInterrupt:
        print("\n收到终止信号，正在保存数据...")
    finally:
        # 停止监听
        input_monitor.stop()
        # 保存事件历史
        input_monitor.save_events()
        print("测试完成!")


if __name__ == "__main__":


    main()
