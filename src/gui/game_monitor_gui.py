from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QGridLayout, QFrame,
                            QScrollArea, QSizePolicy, QGroupBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class GameMonitorGUI(QMainWindow):
    def __init__(self, game_processor):
        """初始化游戏监控GUI"""
        super().__init__()
        self.processor = game_processor
        self.config_manager = game_processor.config_manager
        
        # 获取需要显示的区域列表，过滤掉未启用状态管理的区域
        self.regions_to_process = [
            name for name in self.config_manager.config.keys()
            if name != 'basic_config' 
            and isinstance(self.config_manager.config[name], dict)
            and self.config_manager.config[name].get('Enabled', False)  # 只显示启用的区域
            # and self.config_manager.config[name].get('state_manager', {}).get('Enabled', True)  # 显示启用了状态管理的区域
        ]
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """设置GUI界面"""
        self.setWindowTitle("游戏状态监控")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                background-color: white;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
            QLabel {
                padding: 5px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)

        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        self.status_grid = QGridLayout(content_widget)
        self.status_grid.setSpacing(10)
        
        # 创建状态标签字典
        self.status_labels = {}
        
        # 为每个区域创建分组框，使用两列布局
        row = 0
        col = 0
        max_cols = 2  # 设置为2列显示
        
        for region in self.regions_to_process:
            region_config = self.config_manager.config.get(region, {})
            region_name_zh = region_config.get('name_zh', region)
            
            # 创建分组框
            group_box = QGroupBox(f"{region_name_zh}")
            group_box.setFont(QFont('Arial', 10, QFont.Bold))
            group_layout = QVBoxLayout()
            
            # 创建状态值标签
            value_label = QLabel("等待更新...")
            value_label.setFont(QFont('Arial', 10))
            value_label.setWordWrap(True)
            value_label.setTextFormat(Qt.PlainText)
            value_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            
            # 根据不同区域类型设置不同的样式
            if "chat" in region.lower():  # 聊天相关区域
                value_label.setMinimumWidth(400)  # 减小宽度以适应两列
                value_label.setMinimumHeight(200)
                group_box.setStyleSheet("QGroupBox { background-color: #E3F2FD; }")
            elif "game" in region.lower():  # 游戏相关区域
                value_label.setMinimumWidth(300)  # 减小宽度以适应两列
                value_label.setMinimumHeight(150)
                group_box.setStyleSheet("QGroupBox { background-color: #F1F8E9; }")
            elif "skill" in region.lower():  # 技能相关区域
                value_label.setMinimumWidth(250)  # 减小宽度以适应两列
                value_label.setMinimumHeight(120)
                group_box.setStyleSheet("QGroupBox { background-color: #E8EAF6; }")
            elif "coordinate" in region.lower():  # 坐标相关区域
                value_label.setMinimumWidth(200)  # 减小宽度以适应两列
                value_label.setMinimumHeight(60)
                group_box.setStyleSheet("QGroupBox { background-color: #FFF3E0; }")
            else:  # 其他区域
                value_label.setMinimumWidth(250)  # 减小宽度以适应两列
                value_label.setMinimumHeight(80)
                group_box.setStyleSheet("QGroupBox { background-color: #FAFAFA; }")
            
            group_layout.addWidget(value_label)
            group_box.setLayout(group_layout)
            
            # 将分组框添加到网格布局，使用两列
            self.status_grid.addWidget(group_box, row, col)
            self.status_labels[region] = value_label
            
            # 更新行列位置
            col += 1
            if col >= max_cols:  # 当达到最大列数时，换行
                col = 0
                row += 1
        
        # 设置列的拉伸因子，使两列均匀分布
        self.status_grid.setColumnStretch(0, 1)
        self.status_grid.setColumnStretch(1, 1)
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # 创建控制按钮区域
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 10, 0, 10)
        
        # 创建按钮
        start_button = QPushButton("开始监控")
        stop_button = QPushButton("停止监控")
        start_button.setFont(QFont('Arial', 10))
        stop_button.setFont(QFont('Arial', 10))
        
        start_button.clicked.connect(self.start_monitoring)
        stop_button.clicked.connect(self.stop_monitoring)
        
        control_layout.addStretch()
        control_layout.addWidget(start_button)
        control_layout.addWidget(stop_button)
        control_layout.addStretch()
        
        main_layout.addWidget(control_widget)
        
    def setup_timer(self):
        """设置定时器用于更新状态"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.setInterval(1000)  # 每5秒更新一次   
    def start_monitoring(self):
        """开始监控"""
        self.update_timer.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.update_timer.stop()
        
    def update_status(self):
        """更新状态显示"""
        try:
            # 处理一帧并获取结果
            processed_data = self.processor.process_frame(self.regions_to_process)
            
            # 更新显示
            for region, label in self.status_labels.items():
                if region in processed_data:
                    value = processed_data[region]
                    display_value = ""
                    
                    # 根据不同区域显示不同格式
                    if region == "title_area":
                        display_value = f"日期: {value.get('date', '')}\n时间: {value.get('time', '')}\n毫秒: {value.get('ms', '')}"
                    
                    elif region == "game_area":
                        name_groups = value.get('name_groups', [])
                        if name_groups:
                            names = [f"{group['text']} ({group['center_x']},{group['center_y']})"
                                    for group in name_groups]
                            display_value = '\n'.join(names)
                        else:
                            display_value = str(value)
                    
                    elif region == "chat_messages":
                        if 'messages' in value and isinstance(value['messages'], list):
                            display_value = '\n'.join(value['messages'])
                        elif 'combined_text' in value:
                            display_value = value['combined_text']
                        else:
                            display_value = str(value)
                    
                    elif region == "active_skills":
                        if 'active_skills' in value and isinstance(value['active_skills'], list):
                            display_value = '\n'.join(value['active_skills'])
                        elif 'all_active_skills' in value:
                            display_value = value['all_active_skills'].replace('|', '\n')
                        else:
                            display_value = str(value)
                    
                    elif region == "char_coordinates":
                        display_value = f"X: {value.get('x', '')}, Y: {value.get('y', '')}"
                    
                    else:
                        # 尝试智能格式化显示
                        if isinstance(value, dict):
                            # 将字典格式化为多行文本
                            lines = []
                            for k, v in value.items():
                                if isinstance(v, list):
                                    lines.append(f"{k}:")
                                    lines.extend(f"  {item}" for item in v)
                                else:
                                    lines.append(f"{k}: {v}")
                            display_value = '\n'.join(lines)
                        elif isinstance(value, list):
                            # 列表项分行显示
                            display_value = '\n'.join(str(item) for item in value)
                        else:
                            display_value = str(value)
                    
                    label.setText(display_value)
                    label.setStyleSheet("color: black;")
                else:
                    label.setText("无数据")
                    label.setStyleSheet("color: gray;")
                    
        except Exception as e:
            for label in self.status_labels.values():
                label.setText(f"更新失败: {str(e)}")
                label.setStyleSheet("color: red;")