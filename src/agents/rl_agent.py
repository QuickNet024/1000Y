import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from src.agents.base_agent import BaseAgent
from src.models.cnn_model import CNNFeatureExtractor

class RLAgent(BaseAgent):
    """强化学习智能体"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # 初始化模型
        self.feature_extractor = CNNFeatureExtractor(config).to(self.device)
        self.optimizer = torch.optim.Adam(
            self.feature_extractor.parameters(),
            lr=config.get("learning_rate", 0.001)
        )
        
        # 创建模型保存目录
        self.model_dir = Path(config.get("model_dir", "models/saved"))
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def act(self, state):
        """根据状态选择动作
        
        Args:
            state: 环境状态
            
        Returns:
            action: 选择的动作
        """
        # 将状态转换为tensor
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # 提取特征
        with torch.no_grad():
            features = self.feature_extractor(state)
            
        # TODO: 基于特征选择动作
        action = np.random.randint(0, 10)  # 临时使用随机动作
        return action
        
    def train(self):
        """训练智能体"""
        # TODO: 实现训练逻辑
        self.feature_extractor.train()
        print("开始训练...")
        
    def save(self, path):
        """保存模型
        
        Args:
            path: 保存路径
        """
        save_path = self.model_dir / path
        torch.save({
            'feature_extractor_state_dict': self.feature_extractor.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, save_path)
        
    def load(self, path):
        """加载模型
        
        Args:
            path: 模型路径
        """
        checkpoint = torch.load(path)
        self.feature_extractor.load_state_dict(checkpoint['feature_extractor_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict']) 