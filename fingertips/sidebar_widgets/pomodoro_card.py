import math
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide2.QtGui import QPainter, QFont, QColor, QPen, QBrush, QLinearGradient
from PySide2.QtWidgets import QSizePolicy
import qtawesome
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget
from fingertips.notification import show_notification


class CircularProgressBar(QtWidgets.QWidget):
    """圆形进度条组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        
        # 进度条属性
        self._progress = 0  # 0-100
        self.max_value = 100
        self.is_work_mode = True
        
        # 动画
        self.animation = QPropertyAnimation(self, b"progress")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def get_progress(self):
        return self._progress
    
    def set_progress(self, value):
        self._progress = value
        self.update()
    
    progress = QtCore.Property(int, get_progress, set_progress)
    
    def set_progress_animated(self, value):
        """动画设置进度"""
        self.animation.setStartValue(self.progress)
        self.animation.setEndValue(value)
        self.animation.start()
    
    def set_work_mode(self, is_work):
        """设置工作模式"""
        self.is_work_mode = is_work
        self.update()
    
    def paintEvent(self, event):
        """绘制圆形进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 20
        
        # 绘制背景圆环
        painter.setPen(QPen(QColor(240, 240, 240), 8))
        painter.drawEllipse(center, radius, radius)
        
        # 绘制进度圆环
        if self.is_work_mode:
            # 工作模式：红色渐变
            gradient = QLinearGradient(center.x() - radius, center.y() - radius,
                                     center.x() + radius, center.y() + radius)
            gradient.setColorAt(0, QColor(255, 107, 107))
            gradient.setColorAt(1, QColor(255, 64, 129))
        else:
            # 休息模式：绿色渐变
            gradient = QLinearGradient(center.x() - radius, center.y() - radius,
                                     center.x() + radius, center.y() + radius)
            gradient.setColorAt(0, QColor(76, 175, 80))
            gradient.setColorAt(1, QColor(139, 195, 74))
        
        pen = QPen(QBrush(gradient), 8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # 计算进度角度
        angle = int(self.progress * 360 / 100)
        painter.drawArc(center.x() - radius, center.y() - radius, 
                       radius * 2, radius * 2, 90 * 16, -angle * 16)


class PomodoroCard(SidebarWidget):
    """美观简约的番茄钟组件"""
    
    name = '番茄钟'
    category = '生活'
    icon = 'fa.clock-o'
    description = '经典的番茄工作法计时器，25分钟工作 + 5分钟休息'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 番茄钟配置
        self.work_duration = 25 * 60  # 25分钟工作时间
        self.break_duration = 5 * 60  # 5分钟休息时间
        
        # 当前状态
        self.is_running = False
        self.is_work_mode = True
        self.remaining_time = self.work_duration
        self.completed_cycles = 0
        
        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setMinimumSize(280, 320)
        self.setMaximumSize(350, 400)
        self.resize(300, 350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 设置背景样式
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
            }
        """)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 标题区域
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 状态指示器
        self.status_indicator = QtWidgets.QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setStyleSheet("""
            QLabel {
                background-color: #ff6b6b;
                border-radius: 6px;
                border: 2px solid #ffffff;
            }
        """)
        
        # 状态文本
        self.status_label = QtWidgets.QLabel('工作时间')
        self.status_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        title_layout.addWidget(self.status_indicator)
        title_layout.addWidget(self.status_label)
        title_layout.addStretch()
        
        # 完成周期计数
        self.cycle_label = QtWidgets.QLabel('0 个周期')
        self.cycle_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                background: transparent;
            }
        """)
        title_layout.addWidget(self.cycle_label)
        
        main_layout.addLayout(title_layout)
        
        # 进度条区域
        progress_layout = QtWidgets.QHBoxLayout()
        progress_layout.setAlignment(Qt.AlignCenter)
        
        # 创建进度条容器
        progress_container = QtWidgets.QWidget()
        progress_container.setFixedSize(180, 180)
        progress_container_layout = QtWidgets.QVBoxLayout(progress_container)
        progress_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 圆形进度条
        self.progress_bar = CircularProgressBar()
        progress_container_layout.addWidget(self.progress_bar)
        
        # 时间显示（覆盖在进度条上）
        self.time_label = QtWidgets.QLabel('25:00')
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 32px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        self.time_label.setGeometry(0, 0, 180, 180)
        
        # 使用堆叠布局来重叠进度条和时间
        stacked_widget = QtWidgets.QStackedWidget()
        stacked_widget.setFixedSize(180, 180)
        
        # 创建容器来放置进度条和时间标签
        combined_widget = QtWidgets.QWidget()
        combined_layout = QtWidgets.QVBoxLayout(combined_widget)
        combined_layout.setContentsMargins(0, 0, 0, 0)
        combined_layout.addWidget(self.progress_bar)
        
        # 将时间标签放在进度条上方
        self.time_label.setParent(combined_widget)
        self.time_label.setGeometry(0, 65, 180, 50)
        
        stacked_widget.addWidget(combined_widget)
        
        progress_layout.addWidget(stacked_widget)
        main_layout.addLayout(progress_layout)
        
        # 控制按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 开始/暂停按钮
        self.play_pause_button = QtWidgets.QPushButton()
        self.play_pause_button.setFixedSize(60, 60)
        self.play_pause_button.setIcon(qtawesome.icon('fa.play', color='white'))
        self.play_pause_button.setIconSize(QtCore.QSize(24, 24))
        self.play_pause_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: none;
                border-radius: 30px;
                font-size: 18px;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3d8b40, stop:1 #357a35);
            }
        """)
        self.play_pause_button.clicked.connect(self.toggle_timer)
        
        # 重置按钮
        self.reset_button = QtWidgets.QPushButton()
        self.reset_button.setFixedSize(50, 50)
        self.reset_button.setIcon(qtawesome.icon('fa.refresh', color='white'))
        self.reset_button.setIconSize(QtCore.QSize(20, 20))
        self.reset_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff6b6b, stop:1 #ff5252);
                border: none;
                border-radius: 25px;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff5252, stop:1 #f44336);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f44336, stop:1 #e53935);
            }
        """)
        self.reset_button.clicked.connect(self.reset_timer)
        
        button_layout.addStretch()
        button_layout.addWidget(self.play_pause_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 添加底部空间
        main_layout.addStretch()
        
    def update_display(self):
        """更新显示"""
        # 更新时间显示
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # 更新进度条
        total_time = self.work_duration if self.is_work_mode else self.break_duration
        progress = int((total_time - self.remaining_time) * 100 / total_time)
        self.progress_bar.set_progress_animated(progress)
        
        # 更新状态指示器和标签
        if self.is_work_mode:
            self.status_label.setText('工作时间')
            self.status_indicator.setStyleSheet("""
                QLabel {
                    background-color: #ff6b6b;
                    border-radius: 6px;
                    border: 2px solid #ffffff;
                }
            """)
        else:
            self.status_label.setText('休息时间')
            self.status_indicator.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    border-radius: 6px;
                    border: 2px solid #ffffff;
                }
            """)
        
        # 更新进度条模式
        self.progress_bar.set_work_mode(self.is_work_mode)
        
        # 更新完成周期数
        self.cycle_label.setText(f"{self.completed_cycles} 个周期")
        
        # 更新按钮状态
        if self.is_running:
            self.play_pause_button.setIcon(qtawesome.icon('fa.pause', color='white'))
        else:
            self.play_pause_button.setIcon(qtawesome.icon('fa.play', color='white'))
    
    def toggle_timer(self):
        """切换定时器状态"""
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            
            # 显示暂停通知
            mode_text = "工作" if self.is_work_mode else "休息"
            show_notification(
                title="⏸️ 计时器已暂停",
                message=f"{mode_text}时间已暂停，点击继续按钮恢复计时。",
                icon_name="fa.pause-circle",
                auto_close_time=3000  # 3秒后自动关闭
            )
        else:
            self.timer.start(1000)  # 每秒更新一次
            self.is_running = True
            
            # 显示开始通知
            mode_text = "工作" if self.is_work_mode else "休息"
            minutes = self.remaining_time // 60
            show_notification(
                title=f"🍅 {mode_text}时间开始！",
                message=f"{mode_text}时间已开始，剩余 {minutes} 分钟。保持专注！",
                icon_name="fa.play-circle",
                auto_close_time=3000  # 3秒后自动关闭
            )
        
        self.update_display()
        self.save_config_signal.emit()
    
    def reset_timer(self):
        """重置定时器"""
        self.timer.stop()
        self.is_running = False
        self.is_work_mode = True
        self.remaining_time = self.work_duration
        
        # 显示重置通知
        show_notification(
            title="🔄 番茄钟已重置",
            message=f"计时器已重置为 {self.work_duration//60} 分钟工作时间，准备开始新的番茄钟！",
            icon_name="fa.refresh",
            auto_close_time=3000  # 3秒后自动关闭
        )
        
        self.update_display()
        self.save_config_signal.emit()
    
    def update_timer(self):
        """更新定时器"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_display()
        else:
            # 时间到了，切换模式
            self.switch_mode()
    
    def switch_mode(self):
        """切换工作/休息模式"""
        if self.is_work_mode:
            # 从工作模式切换到休息模式
            self.is_work_mode = False
            self.remaining_time = self.break_duration
            self.completed_cycles += 1
            
            # 显示工作完成通知
            show_notification(
                title="🍅 工作时间结束！",
                message=f"恭喜完成第 {self.completed_cycles} 个番茄钟！现在开始 {self.break_duration//60} 分钟休息时间。",
                icon_name="fa.check-circle",
                auto_close_time=8000  # 8秒后自动关闭
            )
        else:
            # 从休息模式切换到工作模式
            self.is_work_mode = True
            self.remaining_time = self.work_duration
            
            # 显示休息结束通知
            show_notification(
                title="⏰ 休息时间结束！",
                message=f"休息时间结束，准备开始新的 {self.work_duration//60} 分钟工作时间。保持专注！",
                icon_name="fa.play-circle",
                auto_close_time=8000  # 8秒后自动关闭
            )
        
        self.update_display()
        self.save_config_signal.emit()
    
    def get_config(self):
        """获取配置"""
        return {
            'work_duration': self.work_duration,
            'break_duration': self.break_duration,
            'is_work_mode': self.is_work_mode,
            'remaining_time': self.remaining_time,
            'completed_cycles': self.completed_cycles,
            'is_running': False  # 重启时总是停止状态
        }
    
    def set_config(self, config):
        """设置配置"""
        self.work_duration = config.get('work_duration', 25 * 60)
        self.break_duration = config.get('break_duration', 5 * 60)
        self.is_work_mode = config.get('is_work_mode', True)
        self.remaining_time = config.get('remaining_time', self.work_duration)
        self.completed_cycles = config.get('completed_cycles', 0)
        self.is_running = False  # 重启时总是停止状态
        
        self.update_display()
