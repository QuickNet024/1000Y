import time
import argparse
import logging
from pathlib import Path
from src.data.collector import DataCollector
from src.agents.rl_agent import RLAgent

from examples.screen_split_demo import GameScreenProcessor
from src.utils.config_manager import ConfigManager
from src.utils.config_parser import ConfigParser
from src.environment.window_manager import WindowManager
from src.utils.logger_manager import LoggerManager

logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AI游戏智能体')
    parser.add_argument('--mode', type=str, default='train',
                      choices=['train', 'test', 'collect'],
                      help='运行模式: train(训练), test(测试), collect(采集数据)')
    parser.add_argument('--config', type=str, default='config/env/game_config.yaml',
                      help='配置文件路径')
    parser.add_argument('--duration', type=int, default=3600,
                      help='数据采集持续时间(秒),仅在collect模式下有效')
    parser.add_argument('--model_path', type=str, default=None,
                      help='模型加载路径,用于test模式')
    return parser.parse_args()

def train(config):
    """训练模式"""
    logger.info("开始训练模式")
    agent = RLAgent(config)
    agent.train()

def test(config, model_path):
    """测试模式"""
    logger.info("开始测试模式")
    agent = RLAgent(config)
    agent.load(model_path)
    # TODO: 实现测试逻辑

def collect_data(config, duration):
    """数据采集模式"""
    logger.info(f"开始数据采集模式,持续时间:{duration}秒")
    collector = DataCollector(config)
    collector.collect_gameplay(duration)

def setup_logging(config):
    """设置日志配置"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_level = getattr(logging, config["logging"]["level"].upper())
    
    # 重新配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                filename=log_dir / f"1000Y_AI_{time.strftime('%Y%m%d_%H%M%S')}.log",
                encoding='utf-8'
            )
        ]
    )

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
 
    # 加载配置
    try:
        config = ConfigParser.parse(args.config)
        
        # 设置日志级别 - 在加载配置后立即设置
        # 初始化窗口管理器并移动窗口
        # 配置文件路径
        basic_config_path = "config/env/status_collection_config.yaml"

        # 使用配置管理器获取日志配置
        config_manager = ConfigManager(basic_config_path)
        logger_config = config_manager.get_logger_config()
        
        # 初始化主程序日志（只初始化一次）
        logger = LoggerManager(
            name='Main',
            **logger_config
        ).get_logger()
        
        # 创建处理器
        processor = GameScreenProcessor(
            config_manager=config_manager,      # 传递配置管理器
            logger=logger                       # 直接传递logger实例       
        )
        # setup_logging(config)
        
        logger.info(f"成功加载配置文件: {args.config}")
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return

    # 获取游戏窗口配置
    game_config = config.get("windows_game", {})
    window_name = game_config.get("window_name")
    screen_config = config.get("screen_data", {})
    monitor = screen_config.get("monitor", {})
    top = monitor.get("top")
    left = monitor.get("left")

    

    
    try:
        
        window_manager = WindowManager(window_name)
        logger.info(f"成功找到游戏窗口: {window_manager.window_title}")
        window_manager.move_window(left, top)
        logger.info(f"已将窗口移动到坐标: ({left}, {top})")
    except Exception as e:
        logger.error(f"窗口操作失败: {e}")
        raise

    # 根据模式执行相应功能
    try:
        if args.mode == 'train':
            train(config)
        elif args.mode == 'test':
            if not args.model_path:
                logger.error("测试模式需要指定模型路径 --model_path")
                return
            test(config, args.model_path)
        elif args.mode == 'collect':
            collect_data(config, args.duration)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"运行出错: {e}")
    finally:
        logger.info("程序结束")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main() 