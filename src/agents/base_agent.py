from abc import ABC, abstractmethod
import torch
import numpy as np

class BaseAgent(ABC):
    """智能体基类,定义基本接口"""
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    @abstractmethod
    def act(self, state):
        """根据状态返回动作"""
        pass
        
    @abstractmethod
    def train(self):
        """训练智能体"""
        pass
    
    @abstractmethod
    def save(self, path):
        """保存模型"""
        pass
    
    @abstractmethod 
    def load(self, path):
        """加载模型"""
        pass 