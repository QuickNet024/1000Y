# 人工智能体结构总览（优化版）

## 1. 总体架构概览

人工智能体由输入模块、核心网络模块、输出模块以及目标函数与优化模块组成，其架构逻辑如下：

- **输入模块**：接收多维度的游戏信息，包括地图、单位状态、全局状态和历史时间步信息
- **核心网络模块**：通过特征提取、时间序列处理以及模块化决策生成最优动作
- **输出模块**：细化到具体动作类型、执行方式和目标
- **目标函数与优化模块**：通过奖励设计和强化学习联合优化模型性能

## 2. 模型输入模块

### 输入特征的四大维度：

#### 地图空间特征
- 包括地形、单位相对位置、障碍物、资源点等信息
- 使用卷积神经网络（CNN）或 Transformer 提取空间关系

#### 单位状态特征
- 包括友方单位和敌方单位的属性（血量、蓝量、攻击范围、状态效果等）
- 通过注意力机制动态聚焦关键单位

#### 全局状态特征
- 包括时间进度、总资源情况、胜负条件进度等宏观信息
- 使用全连接层提取高层次特征

#### 历史时间步信息
- 记录过去的游戏动作和状态变化
- 使用 LSTM/GRU 捕捉时间依赖性，建模历史行为对当前决策的影响

## 3. 核心网络及决策模块

核心网络模块对输入的多维信息进行整合处理，生成最优动作决策。

### 3.1 输入特征处理
- 全局特征处理：通过全连接网络提取高维特征
- 地图特征提取：使用卷积网络提取局部空间特征，或通过 Transformer 捕获长距离依赖关系
- 单位特征提取：利用多头注意力机制动态聚焦关键单位（如优先攻击敌方输出单位）
- 时间序列处理：通过 LSTM/GRU 建模时间步之间的关联

### 3.2 动作分解与模块化决策

将动作分解为以下三部分，由独立的子网络进行预测：

- **What（动作类型）**：当前执行的行为（如移动、攻击、释放技能）
- **How（动作细节）**：具体执行方式（如技能选择、攻击方式）
- **Who（动作目标）**：选择具体目标单位或位置（如攻击目标、移动位置）

这种模块化设计增强了模型的灵活性，适配复杂的游戏场景。

### 3.3 决策逻辑与优化
- 核心策略：基于当前状态，选择最优动作 `at=π(st)`，策略网络学习输出动作概率分布
- 动作价值函数：通过 `Q(s,a)` 估计当前动作的长期收益，用于指导策略优化
- 联合优化：结合即时奖励和长期奖励（如胜负条件）优化模型性能

## 4. 模型输出模块

输出模块基于核心网络的特征处理，生成具体的动作决策：

### 动作类型（What）
- 多分类输出（如"移动""攻击""释放技能"等）

### 动作细节（How）
- 对动作进一步细化（如选择使用哪种技能）

### 目标选择（Who）
- 选择具体目标单位或地图位置

通过联合输出三种动作信息，实现智能体的高效决策。

## 5. 目标函数与优化模块

### 5.1 奖励设计

结合即时奖励和长期奖励设计目标函数：

#### 即时奖励（短期目标）
- 击杀敌方单位：+10 分
- 躲避攻击：+5 分
- 占领资源点：+8 分

#### 长期奖励（全局目标）
- 获得胜利：+100 分
- 完成任务目标（如保护单位存活）：+50 分

### 5.2 联合优化目标
- 强化学习价值优化：通过 `Q(s,a)` 估计动作的长期回报
- 策略梯度优化：基于策略 `π(s)` 学习动作分布概率，优化智能体的策略网络

## 6. 训练与对战流程

### 6.1 模型训练
- 模仿学习：使用人类玩家的游戏数据，快速初始化智能体策略
- 强化学习：通过自我对战，探索更多可能性，优化长期策略

### 6.2 模型对战
- 训练完成后，模型智能体可与人类玩家或其他模型对战
- 动作响应时间优化至 193ms 内，接近人类玩家的操作速度

## 7. 核心模块伪代码

以下是核心决策网络的 PyTorch 伪代码：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class CoreDecisionNetwork(nn.Module):
    def __init__(self, state_dim, action_dims, hidden_dim=256):
        super(CoreDecisionNetwork, self).__init__()
        
        # 全局状态特征处理
        self.global_fc = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # 局部地图特征提取
        self.local_conv = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Flatten()
        )
        
        # 单位特征注意力处理
        self.unit_attention = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=4)
        
        # 时间序列处理
        self.gru = nn.GRU(input_size=hidden_dim, hidden_size=hidden_dim, batch_first=True)
        
        # 动作输出模块
        self.action_type_head = nn.Linear(hidden_dim, action_dims['action_type'])  # What
        self.action_detail_head = nn.Linear(hidden_dim, action_dims['action_detail'])  # How
        self.action_target_head = nn.Linear(hidden_dim, action_dims['action_target'])  # Who

    def forward(self, global_state, local_map, unit_states, history_states):
        # 全局特征处理
        global_features = self.global_fc(global_state)
        
        # 地图特征处理
        local_features = self.local_conv(local_map)
        
        # 单位特征处理
        unit_states = unit_states.permute(1, 0, 2)  # 调整维度以适配注意力机制
        unit_features, _ = self.unit_attention(unit_states, unit_states, unit_states)
        unit_features = torch.mean(unit_features, dim=0)
        
        # 时间序列特征处理
        _, hidden_state = self.gru(history_states)
        time_features = hidden_state[-1]
        
        # 综合特征融合
        combined_features = global_features + local_features + unit_features + time_features
        
        # 动作决策输出
        action_type = self.action_type_head(combined_features)  # 动作类型
        action_detail = self.action_detail_head(combined_features)  # 动作细节
        action_target = self.action_target_head(combined_features)  # 动作目标
        
        return action_type, action_detail, action_target
```

## 8. 优化亮点

- **模块化设计**：动作分解为多部分（What、How、Who），提升策略灵活性
- **特征增强**：融合全局、局部、单位与时间序列特征，提升决策能力
- **联合奖励优化**：结合短期与长期目标，指导智能体策略更全面