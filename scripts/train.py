import argparse
from pathlib import Path
from src.utils.config_parser import ConfigParser
from src.agents.base_agent import BaseAgent
# 根据需要导入其他模块

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True, help="配置文件路径")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 加载配置
    config = ConfigParser.parse(args.config)
    
    # 创建智能体
    agent = BaseAgent(config)
    
    # 开始训练
    agent.train()
    
if __name__ == "__main__":
    main() 