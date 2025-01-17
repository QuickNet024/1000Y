import sys
import cv2
import numpy as np
import pyautogui
from paddleocr import PaddleOCR
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPainter, QPen, QColor, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from pynput import keyboard

# 初始化PaddleOCR
ocr = PaddleOCR(
    use_angle_cls=False,  # 关闭方向分类，因为都是正向文本
    lang='ch',
    det_model_dir='F:/2025Projects/1000Y/models/PP-OCRv4_det',  # 使用PP-OCRv4检测模型
    rec_model_dir='F:/2025Projects/1000Y/models/ch_PP-OCRv4_rec_infer',  # 使用PP-OCRv4识别模型
    det_limit_side_len=960,  # 限制最长边，避免图片过大
    det_db_thresh=0.3,  # 降低检测阈值，提高对小文字的敏感度
    det_db_box_thresh=0.3,  # 降低检测框阈值
    det_db_unclip_ratio=1.6,  # 调整文本框扩张比例
    use_gpu=True,        # 使用GPU
    rec_batch_num=1      # 单张图片识别
)


class HotKeyHandler(QObject):
    toggle_signal = pyqtSignal()  # 创建信号

    def __init__(self):
        super().__init__()
        self.setup_hotkey()

    def setup_hotkey(self):
        def on_activate():
            self.toggle_signal.emit()  # 发送信号

        def for_canonical(f):
            return lambda k: f(self.listener.canonical(k))

        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>+<alt>+1'),
            on_activate)
        self.listener = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release))
        self.listener.start()

    def stop_listener(self):
        self.listener.stop()

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标题标签
        self.title = QLabel("OCR Detection Window (ESC to exit)")
        self.title.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.title)
        self.setLayout(layout)
        self.setFixedHeight(30)
        
        self.start = QPoint(0, 0)
        self.pressing = False

    def mousePressEvent(self, event):
        self.start = self.mapToGlobal(event.pos())
        self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            self.end = self.mapToGlobal(event.pos())
            self.movement = self.end - self.start
            self.parent.move(
                self.parent.x() + self.movement.x(),
                self.parent.y() + self.movement.y()
            )
            self.start = self.end

    def mouseReleaseEvent(self, event):
        self.pressing = False

class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.ocr_results = None
        self.resizing = False
        self.resize_margin = 5
        self.is_recognizing = False
        
        # 创建热键处理器
        self.hotkey_handler = HotKeyHandler()
        self.hotkey_handler.toggle_signal.connect(self.toggle_recognition)
        
    def toggle_recognition(self):
        self.is_recognizing = not self.is_recognizing
        if self.is_recognizing:
            self.timer.start(100)
            self.title_bar.title.setText("OCR Detection Window (Running... ESC to exit)")
        else:
            self.timer.stop()
            self.title_bar.title.setText("OCR Detection Window (Stopped. ESC to exit)")

    def initUI(self):
        self.setWindowTitle('OCR Detection')
        self.setGeometry(100, 100, 1024, 768)
        
        # 设置窗口标志
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 添加标题栏
        self.title_bar = TitleBar(self)
        layout.addWidget(self.title_bar)
        layout.addStretch()  # 添加弹性空间
        
        self.setLayout(layout)
        
        # 定时器用于定期更新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.stop()

    def update_frame(self):
        if not self.is_recognizing:
            return
        # 截取桌面图像
        screenshot = pyautogui.screenshot(region=(self.x(), self.y(), self.width(), self.height()))
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 图像预处理
        # 1. 放大图像
        scale = 2.0  # 放大2倍
        frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # 2. 图像增强
        # 提高对比度
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        frame = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # 3. 锐化
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        frame = cv2.filter2D(frame, -1, kernel)
        
        # 执行OCR识别
        self.ocr_results = ocr.ocr(frame, cls=False)
        
        # 如果有结果，需要将坐标缩放回原始大小
        if self.ocr_results:
            scaled_results = []
            for line in self.ocr_results:
                if line is None:
                    continue
                scaled_line = []
                for result in line:
                    if result is None:
                        continue
                    points, (text, confidence) = result
                    # 将坐标缩放回原始大小
                    scaled_points = [[int(x/scale), int(y/scale)] for x, y in points]
                    scaled_line.append([scaled_points, (text, confidence)])
                scaled_results.append(scaled_line)
            self.ocr_results = scaled_results
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        
        # 绘制边框
        pen = QPen(Qt.gray, 2, Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRect(self.rect())
        
        # 绘制调整大小的角落标记
        painter.drawRect(self.width() - 20, self.height() - 20, 20, 20)
        
        if self.is_recognizing and self.ocr_results:
            # 设置OCR检测框的画笔
            pen = QPen(Qt.green, 2, Qt.SolidLine)
            painter.setPen(pen)
            
            for line in self.ocr_results:
                if line is None:
                    continue
                for result in line:
                    if result is None:
                        continue
                    try:
                        points = result[0]
                        for i in range(4):
                            x1, y1 = points[i]
                            x2, y2 = points[(i + 1) % 4]
                            painter.drawLine(
                                int(x1), int(y1),
                                int(x2), int(y2)
                            )
                    except Exception as e:
                        print(f"Error drawing box: {e}")
                        continue

    def mousePressEvent(self, event):
        if event.pos().y() > self.title_bar.height():  # 不在标题栏区域
            if event.pos().x() > self.width() - 20 and event.pos().y() > self.height() - 20:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()

    def mouseMoveEvent(self, event):
        # 更新鼠标样式
        if event.pos().x() > self.width() - 20 and event.pos().y() > self.height() - 20:
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        # 处理调整大小
        if self.resizing:
            diff = event.globalPos() - self.resize_start_pos
            new_geometry = self.resize_start_geometry
            new_width = new_geometry.width() + diff.x()
            new_height = new_geometry.height() + diff.y()
            if new_width > 100 and new_height > 100:  # 最小尺寸限制
                self.setGeometry(new_geometry.x(), new_geometry.y(), new_width, new_height)

    def mouseReleaseEvent(self, event):
        self.resizing = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.hotkey_handler.stop_listener()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
