import torch
import torch.nn as nn

class CNNFeatureExtractor(nn.Module):
    """CNN特征提取模型"""
    
    def __init__(self, config):
        super().__init__()
        
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU()
        )
        
        self.fc = nn.Sequential(
            nn.Linear(self._get_conv_output_size(), 512),
            nn.ReLU()
        )
        
    def _get_conv_output_size(self):
        # 计算卷积层输出大小
        x = torch.randn(1, 3, 84, 84)
        x = self.conv_layers(x)
        return x.view(1, -1).size(1)
        
    def forward(self, x):
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        return self.fc(x) 