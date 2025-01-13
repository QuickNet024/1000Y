# 项目目录结构说明文档

## 目录结构

```
├── config/                          # 配置文件目录
│   ├── env/                         # 环境配置
│   │   ├── game_config.yaml        # 游戏环境配置
│   │   └── screen_config.yaml      # 屏幕捕获配置
│   ├── model/                      # 模型配置
│   │   ├── cnn_config.yaml        # CNN模型配置
│   │   ├── lstm_config.yaml       # LSTM模型配置
│   │   └── rl_config.yaml         # 强化学习配置
│   └── train/                      # 训练配置
│       ├── sl_config.yaml         # 监督学习配置
│       └── optimizer_config.yaml   # 优化器配置
│
├── data/                           # 数据目录
│   ├── raw/                        # 原始数据
│   │   ├── screenshots/            # 游戏截图
│   │   ├── actions/               # 玩家操作记录
│   │   └── states/                # 游戏状态记录
│   ├── processed/                  # 处理后的数据
│   │   ├── features/              # 特征数据
│   │   ├── labels/                # 标签数据
│   │   └── sequences/             # 时序数据
│   └── temp/                       # 临时数据
│
├── src/                           # 源代码目录
│   ├── agents/                    # 智能体模块
│   │   ├── __init__.py
│   │   ├── base_agent.py         # 基础智能体
│   │   ├── rl_agent.py          # 强化学习智能体
│   │   └── sl_agent.py          # 监督学习智能体
│   │
│   ├── environment/              # 环境交互模块
│   │   ├── __init__.py
│   │   ├── screen_splitter.py    # 屏幕分割  
│   │   ├── screen_capture.py    # 屏幕捕获
│   │   ├── input_control.py     # 输入控制
│   │   ├── data_processor.py    # 数据处理 
│   │   ├── image_preprocessor.py    # 图像预处理
│   │   ├── state_manager.py    # 状态管理
│   │   └── game_state.py        # 游戏状态解析
│   │
│   ├── models/                   # 模型定义模块
│   │   ├── __init__.py
│   │   ├── cnn_model.py         # CNN特征提取模型
│   │   ├── lstm_model.py        # LSTM时序模型
│   │   ├── decision_model.py    # 决策模型
│   │   └── value_model.py       # 价值评估模型
│   │
│   ├── data/                     # 数据处理模块
│   │   ├── __init__.py
│   │   ├── collector.py         # 数据采集
│   │   ├── processor.py         # 数据预处理
│   │   └── dataset.py          # 数据集定义
│   │
│   ├── training/                # 训练模块
│   │   ├── __init__.py
│   │   ├── trainer.py          # 训练器
│   │   ├── evaluator.py        # 评估器
│   │   └── optimizer.py        # 优化器
│   │
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       ├── logger.py           # 日志工具
│       ├── visualizer.py       # 可视化工具
│       └── config_parser.py    # 配置解析工具
│
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_agents/            # 智能体测试
│   ├── test_environment/       # 环境测试
│   └── test_models/           # 模型测试
│
├── notebooks/                  # Jupyter笔记本目录
│   ├── data_analysis.ipynb    # 数据分析
│   ├── model_evaluation.ipynb # 模型评估
│   └── visualization.ipynb    # 可视化分析
│
├── logs/                      # 日志目录
│   ├── training/             # 训练日志
│   └── runtime/              # 运行日志
│
├── models/                   # 模型保存目录
│   ├── checkpoints/         # 模型检查点
│   └── saved/              # 已训练模型
│
├── docs/                    # 文档目录
│   ├── api/                # API文档
│   └── guides/            # 使用指南
│
├── scripts/                # 脚本目录
│   ├── train.py           # 训练脚本
│   ├── evaluate.py        # 评估脚本
│   └── run.py            # 运行脚本
│
├── .gitignore            # Git忽略文件
├── requirements.txt        # 依赖包列表
├── setup.py              # 安装配置
└── README.md             # 项目说明
```

## 目录说明

### 1. config/ - 配置文件目录
- **env/**: 环境相关配置
  - `game_config.yaml`: 游戏参数配置
  - `screen_config.yaml`: 屏幕捕获参数
- **model/**: 模型相关配置
  - `cnn_config.yaml`: CNN模型架构配置
  - `lstm_config.yaml`: LSTM模型参数配置
  - `rl_config.yaml`: 强化学习算法配置
- **train/**: 训练相关配置
  - `sl_config.yaml`: 监督学习参数
  - `optimizer_config.yaml`: 优化器参数

### 2. data/ - 数据目录
- **raw/**: 原始数据存储
  - `screenshots/`: 游戏截图
  - `actions/`: 玩家操作记录
  - `states/`: 游戏状态记录
- **processed/**: 处理后的数据
  - `features/`: 提取的特征数据
  - `labels/`: 标签数据
  - `sequences/`: 时序数据序列
- **temp/**: 临时数据存储

### 3. src/ - 源代码目录
- **agents/**: 智能体实现
  - `base_agent.py`: 基础智能体类
  - `rl_agent.py`: 强化学习智能体
  - `sl_agent.py`: 监督学习智能体
- **environment/**: 环境交互
  - `screen_capture.py`: 屏幕捕获实现
  - `input_control.py`: 输入控制实现
  - `game_state.py`: 游戏状态解析
  - `screen_splitter.py`: 屏幕分割
  - `text_recognizer.py`: 文本识别
  - `image_preprocessor.py`: 图像预处理
  - `data_processor.py`: 数据处理
  - `state_manager.py`: 状态管理  
- **models/**: 模型定义
  - `cnn_model.py`: CNN模型架构
  - `lstm_model.py`: LSTM模型架构
  - `decision_model.py`: 决策模型
  - `value_model.py`: 价值评估模型
- **data/**: 数据处理
  - `collector.py`: 数据采集实现
  - `processor.py`: 数据预处理实现
  - `dataset.py`: 数据集类定义
- **training/**: 训练相关
  - `trainer.py`: 训练器实现
  - `evaluator.py`: 评估器实现
  - `optimizer.py`: 优化器实现
- **utils/**: 工具函数
  - `logger.py`: 日志工具
  - `visualizer.py`: 可视化工具
  - `config_parser.py`: 配置解析工具

### 4. tests/ - 测试目录
- 包含各模块的单元测试和集成测试

### 5. notebooks/ - Jupyter笔记本
- 用于数据分析和模型评估的交互式笔记本

### 6. logs/ - 日志目录
- **training/**: 训练过程日志
- **runtime/**: 运行时日志

### 7. models/ - 模型存储
- **checkpoints/**: 训练过程检查点
- **saved/**: 最终训练模型

### 8. docs/ - 文档目录
- **api/**: API文档
- **guides/**: 使用指南

### 9. scripts/ - 脚本目录
- `train.py`: 训练入口脚本
- `evaluate.py`: 评估脚本
- `run.py`: 运行入口脚本

## 关键文件说明

1. `requirements.txt`: 列出所有Python依赖包
2. `setup.py`: 项目安装配置文件
3. `activate_env.bat`: 虚拟环境激活脚本
4. `.gitignore`: Git版本控制忽略文件配置
5. `README.md`: 项目总体说明文档

## 使用建议

1. 开发前先查看配置文件目录 `config/`
2. 数据处理流程遵循 `raw/ -> processed/` 的顺序
3. 模型开发参考 `models/` 目录下的基础实现
4. 使用 `notebooks/` 进行实验和分析
5. 通过 `scripts/` 目录下的脚本进行训练和评估

## 扩展建议

1. 新增模型时在 `models/` 下添加相应文件
2. 添加新的数据处理方法在 `data/` 下实现
3. 扩展功能时注意更新配置文件和文档 

## 开发指南

1. 首先激活虚拟环境：
   ```bash
   .\activate_env.bat
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 开发流程：
   - 配置文件修改在 `config/` 目录下进行
   - 新功能开发在 `src/` 目录下对应模块中进行
   - 数据处理遵循 `raw/ -> processed/` 的流程
   - 所有新功能需要在 `tests/` 下添加对应测试

## 注意事项

1. 保持目录结构清晰，遵循模块化原则
2. 定期备份数据和模型
3. 遵循代码规范和文档规范
4. 及时更新文档和测试用例