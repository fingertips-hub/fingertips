import psutil
import qtawesome
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide2.QtGui import QPainter, QPen, QColor, QFont, QLinearGradient
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget


class HorizontalProgressBar(QtWidgets.QWidget):
    """横向进度条组件"""
    
    def __init__(self, height=20, progress_color="#4CAF50", parent=None):
        super().__init__(parent)
        self.height = height
        self.progress_color = QColor(progress_color)
        # 设置透明白色背景
        self.bg_color = QColor(255, 255, 255, 50)  # 白色，透明度约20%
        self.value = 0
        self.max_value = 100
        
        self.setFixedHeight(height)
        self.setMinimumWidth(100)
        
        # 动画效果
        self.animation = QPropertyAnimation(self, b"value_animated")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def set_value(self, value, animated=True):
        """设置进度值"""
        if animated:
            self.animation.setStartValue(self.value)
            self.animation.setEndValue(value)
            self.animation.start()
        else:
            self.value = value
            self.update()
        
    def get_value_animated(self):
        return self.value
        
    def set_value_animated(self, value):
        self.value = value
        self.update()
        
    value_animated = QtCore.Property(float, get_value_animated, set_value_animated)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算进度条区域
        bar_rect = self.rect().adjusted(2, 2, -2, -2)
        
        # 绘制背景 - 使用更透明的白色
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_rect, self.height//4, self.height//4)
        
        # 绘制进度
        if self.value > 0:
            progress_width = int(bar_rect.width() * (self.value / self.max_value))
            progress_rect = QtCore.QRect(bar_rect.x(), bar_rect.y(), progress_width, bar_rect.height())
            
            # 创建渐变效果
            gradient = QLinearGradient(0, 0, progress_width, 0)
            gradient.setColorAt(0, self.progress_color.lighter(120))
            gradient.setColorAt(1, self.progress_color)
            
            painter.setBrush(QtGui.QBrush(gradient))
            painter.drawRoundedRect(progress_rect, self.height//4, self.height//4)


class SystemInfoCard(SidebarWidget):
    """系统信息监控卡片"""
    
    name = '系统监控'
    category = '系统'
    icon = 'fa5s.desktop'
    description = '实时显示CPU、内存、磁盘等系统信息'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        self.update_system_info()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setMinimumSize(320, 450)
        self.setStyleSheet("""
            SystemInfoCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 16px;
                border: none;
            }
        """)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # 标题区域
        self.create_header(main_layout)
        
        # 系统资源区域（CPU、内存、磁盘）
        self.create_system_resources_section(main_layout)
        
        # 网络区域
        self.create_network_section(main_layout)
        
        main_layout.addStretch()
        
    def create_header(self, layout):
        """创建标题区域"""
        header_layout = QtWidgets.QHBoxLayout()
        
        # 图标
        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(qtawesome.icon('fa5s.desktop', color='white').pixmap(24, 24))
        header_layout.addWidget(icon_label)
        
        # 标题
        title_label = QtWidgets.QLabel('系统监控')
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QtWidgets.QPushButton()
        refresh_btn.setIcon(qtawesome.icon('ei.refresh', color='white'))
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        refresh_btn.clicked.connect(self.update_system_info)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
    def create_system_resources_section(self, layout):
        """创建系统资源信息区域（CPU、内存、磁盘）"""
        resources_container = QtWidgets.QWidget()
        resources_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                border: none;
            }
        """)
        
        resources_layout = QtWidgets.QVBoxLayout(resources_container)
        resources_layout.setContentsMargins(15, 15, 15, 15)
        resources_layout.setSpacing(15)
        
        # CPU部分
        cpu_layout = QtWidgets.QVBoxLayout()
        cpu_layout.setSpacing(8)
        
        cpu_header = QtWidgets.QHBoxLayout()
        cpu_icon = QtWidgets.QLabel()
        cpu_icon.setPixmap(qtawesome.icon('fa5s.microchip', color='#FF6B6B').pixmap(16, 16))
        cpu_header.addWidget(cpu_icon)
        
        self.cpu_title = QtWidgets.QLabel('CPU')
        self.cpu_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        cpu_header.addWidget(self.cpu_title)
        
        cpu_header.addStretch()
        
        self.cpu_value = QtWidgets.QLabel('--')
        self.cpu_value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
        """)
        cpu_header.addWidget(self.cpu_value)
        
        cpu_layout.addLayout(cpu_header)
        
        self.cpu_progress = HorizontalProgressBar(height=10, progress_color="#FF6B6B")
        cpu_layout.addWidget(self.cpu_progress)
        
        # CPU详细信息
        cpu_details = QtWidgets.QHBoxLayout()
        self.cpu_cores = QtWidgets.QLabel('核心: --')
        self.cpu_cores.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                background: transparent;
            }
        """)
        cpu_details.addWidget(self.cpu_cores)
        
        cpu_details.addStretch()
        
        self.cpu_freq = QtWidgets.QLabel('频率: --')
        self.cpu_freq.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                background: transparent;
            }
        """)
        cpu_details.addWidget(self.cpu_freq)
        
        cpu_layout.addLayout(cpu_details)
        resources_layout.addLayout(cpu_layout)

        # 内存部分
        memory_layout = QtWidgets.QVBoxLayout()
        memory_layout.setSpacing(8)
        
        memory_header = QtWidgets.QHBoxLayout()
        memory_icon = QtWidgets.QLabel()
        memory_icon.setPixmap(qtawesome.icon('fa5s.memory', color='#4ECDC4').pixmap(16, 16))
        memory_header.addWidget(memory_icon)
        
        self.memory_title = QtWidgets.QLabel('内存')
        self.memory_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        memory_header.addWidget(self.memory_title)
        
        memory_header.addStretch()
        
        self.memory_value = QtWidgets.QLabel('--')
        self.memory_value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
        """)
        memory_header.addWidget(self.memory_value)
        
        memory_layout.addLayout(memory_header)
        
        self.memory_progress = HorizontalProgressBar(height=10, progress_color="#4ECDC4")
        memory_layout.addWidget(self.memory_progress)
        
        self.memory_info = QtWidgets.QLabel('-- / --')
        self.memory_info.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                background: transparent;
            }
        """)
        memory_layout.addWidget(self.memory_info)
        
        resources_layout.addLayout(memory_layout)

        # 磁盘部分
        disk_layout = QtWidgets.QVBoxLayout()
        disk_layout.setSpacing(8)
        
        disk_header = QtWidgets.QHBoxLayout()
        disk_icon = QtWidgets.QLabel()
        disk_icon.setPixmap(qtawesome.icon('fa5s.hdd', color='#FFD93D').pixmap(16, 16))
        disk_header.addWidget(disk_icon)
        
        self.disk_title = QtWidgets.QLabel('磁盘')
        self.disk_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        disk_header.addWidget(self.disk_title)
        
        disk_header.addStretch()
        
        self.disk_value = QtWidgets.QLabel('--')
        self.disk_value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
        """)
        disk_header.addWidget(self.disk_value)
        
        disk_layout.addLayout(disk_header)
        
        self.disk_progress = HorizontalProgressBar(height=10, progress_color="#FFD93D")
        disk_layout.addWidget(self.disk_progress)
        
        self.disk_info = QtWidgets.QLabel('-- / --')
        self.disk_info.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                background: transparent;
            }
        """)
        disk_layout.addWidget(self.disk_info)
        
        resources_layout.addLayout(disk_layout)
        
        layout.addWidget(resources_container)
        
    def create_network_section(self, layout):
        """创建网络信息区域"""
        network_container = QtWidgets.QWidget()
        network_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                border: none;
            }
        """)
        
        network_layout = QtWidgets.QHBoxLayout(network_container)
        network_layout.setContentsMargins(15, 15, 15, 15)
        network_layout.setSpacing(16)
        
        # 网络图标
        network_icon = QtWidgets.QLabel()
        network_icon.setStyleSheet("QLabel {background: transparent;}")
        network_icon.setPixmap(qtawesome.icon('fa5s.wifi', color='white').pixmap(30, 30))
        network_layout.addWidget(network_icon)
        
        # 网络信息
        network_info_layout = QtWidgets.QVBoxLayout()
        network_info_layout.setSpacing(6)
        
        network_title = QtWidgets.QLabel('网络状态')
        network_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        network_info_layout.addWidget(network_title)
        
        self.network_upload = QtWidgets.QLabel('上传: -- KB/s')
        self.network_upload.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                background: transparent;
            }
        """)
        network_info_layout.addWidget(self.network_upload)
        
        self.network_download = QtWidgets.QLabel('下载: -- KB/s')
        self.network_download.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                background: transparent;
            }
        """)
        network_info_layout.addWidget(self.network_download)
        
        network_layout.addLayout(network_info_layout)
        network_layout.addStretch()
        
        layout.addWidget(network_container)
        
    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_system_info)
        self.update_timer.start(2000)  # 每2秒更新一次
        
        # 网络监控需要更频繁的更新
        self.network_timer = QTimer()
        self.network_timer.timeout.connect(self.update_network_info)
        self.network_timer.start(1000)  # 每1秒更新一次
        
        # 存储上次网络数据
        self.last_net_io = psutil.net_io_counters()
        
    def update_system_info(self):
        """更新系统信息"""
        try:
            # 更新CPU信息
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_progress.set_value(cpu_percent)
            self.cpu_value.setText(f"{cpu_percent:.1f}%")
            
            # CPU详细信息
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                freq_text = f"频率: {cpu_freq.current:.0f} MHz"
            else:
                freq_text = "频率: 未知"
            
            self.cpu_cores.setText(f"核心: {cpu_count}")
            self.cpu_freq.setText(freq_text)
            
            # 更新内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = self.format_bytes(memory.used)
            memory_total = self.format_bytes(memory.total)
            
            self.memory_progress.set_value(memory_percent)
            self.memory_value.setText(f"{memory_percent:.0f}%")
            self.memory_info.setText(f"{memory_used} / {memory_total}")
            
            # 更新磁盘信息 (Windows兼容性)
            import os
            if os.name == 'nt':  # Windows
                disk_path = 'C:\\'
            else:  # Unix/Linux/macOS
                disk_path = '/'
                
            disk = psutil.disk_usage(disk_path)
            disk_percent = (disk.used / disk.total) * 100
            disk_used = self.format_bytes(disk.used)
            disk_total = self.format_bytes(disk.total)
            
            self.disk_progress.set_value(disk_percent)
            self.disk_value.setText(f"{disk_percent:.0f}%")
            self.disk_info.setText(f"{disk_used} / {disk_total}")
            
        except Exception as e:
            print(f"更新系统信息时出错: {e}")
            
    def update_network_info(self):
        """更新网络信息"""
        try:
            current_net_io = psutil.net_io_counters()
            
            # 计算网络速度
            upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / 1024  # KB/s
            download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / 1024  # KB/s
            
            self.network_upload.setText(f"上传: {upload_speed:.1f} KB/s")
            self.network_download.setText(f"下载: {download_speed:.1f} KB/s")
            
            self.last_net_io = current_net_io
            
        except Exception as e:
            print(f"更新网络信息时出错: {e}")
            
    def format_bytes(self, bytes_value):
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
        
    def get_config(self):
        """获取配置"""
        return {
            'update_interval': 2000
        }
        
    def set_config(self, config):
        """设置配置"""
        interval = config.get('update_interval', 2000)
        if hasattr(self, 'update_timer'):
            self.update_timer.setInterval(interval) 