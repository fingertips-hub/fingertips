import uuid
from datetime import datetime, timedelta
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QPainter, QPen, QBrush, QColor
import qtawesome
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget


class CountdownItemWidget(QtWidgets.QWidget):
    """单个倒计时项目组件"""
    
    # 信号定义
    item_deleted = QtCore.Signal(str)  # 删除信号，传递ID
    item_edited = QtCore.Signal(str, dict)  # 编辑信号，传递ID和数据
    
    def __init__(self, countdown_id, data, parent=None):
        super().__init__(parent)
        self.countdown_id = countdown_id
        self.title = data.get('title', '倒计时')
        
        # 处理target_time，支持字符串和datetime对象
        target_time_value = data.get('target_time', datetime.now())
        if isinstance(target_time_value, str):
            self.target_time = datetime.fromisoformat(target_time_value)
        elif isinstance(target_time_value, datetime):
            self.target_time = target_time_value
        else:
            self.target_time = datetime.now() + timedelta(days=1)
            
        self.description = data.get('description', '')
        self.color = data.get('color', '#4CAF50')
        
        # 处理开始时间，用于正确计算百分比
        start_time_value = data.get('start_time', data.get('create_time', datetime.now()))  # 向后兼容
        if isinstance(start_time_value, str):
            self.start_time = datetime.fromisoformat(start_time_value)
        elif isinstance(start_time_value, datetime):
            self.start_time = start_time_value
        else:
            self.start_time = datetime.now()
        
        # 卡片状态
        self.is_hovered = False
        
        self.setup_ui()
        self.update_description_display()  # 初始化描述显示
        self.update_display()
        
        # 设置定时器，每秒更新一次
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)  # 1秒更新一次
        
    def setup_ui(self):
        """设置UI界面"""
        self.setFixedHeight(86)
        
        # 设置鼠标跟踪来实现悬停效果
        self.setMouseTracking(True)
        
        # 设置背景透明，这样我们的paintEvent可以正常工作
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(6)
        
        # 顶部：标题和操作按钮
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(8)
        
        # 标题
        self.title_label = QtWidgets.QLabel(self.title)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: #2c3e50;
                background: transparent;
                padding: 2px 0px;
            }}
        """)
        top_layout.addWidget(self.title_label, 1)
        
        # 操作按钮容器
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(4)
        
        # 编辑按钮
        self.edit_button = QtWidgets.QPushButton()
        self.edit_button.setIcon(qtawesome.icon('fa5s.edit', color='#888'))
        self.edit_button.setFixedSize(28, 28)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 14px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 0.1);
                border-color: rgba(76, 175, 80, 0.3);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: rgba(76, 175, 80, 0.2);
                transform: scale(0.95);
            }
        """)
        self.edit_button.clicked.connect(self.edit_countdown)
        button_layout.addWidget(self.edit_button)
        
        # 删除按钮
        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setIcon(qtawesome.icon('fa5s.trash', color='#ff5722'))
        self.delete_button.setFixedSize(28, 28)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 14px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 87, 34, 0.1);
                border-color: rgba(255, 87, 34, 0.3);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: rgba(255, 87, 34, 0.2);
                transform: scale(0.95);
            }
        """)
        self.delete_button.clicked.connect(self.delete_countdown)
        button_layout.addWidget(self.delete_button)
        
        top_layout.addLayout(button_layout)
        main_layout.addLayout(top_layout)
        
        # 进度条
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 0.05);
                text-align: center;
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.color}, stop:0.5 {self._lighten_color(self.color)}, stop:1 {self.color});
            }}
        """)
        main_layout.addWidget(self.progress_bar)
        
        # 时间显示布局
        time_layout = QtWidgets.QHBoxLayout()
        
        # 剩余时间
        self.time_label = QtWidgets.QLabel()
        self.time_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.color};
                background: transparent;
                padding: 1px 0px;
            }}
        """)
        time_layout.addWidget(self.time_label)
        
        time_layout.addStretch()
        
        # 目标时间
        self.target_label = QtWidgets.QLabel()
        self.target_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #7f8c8d;
                background: transparent;
                font-weight: 500;
            }
        """)
        time_layout.addWidget(self.target_label)
        
        main_layout.addLayout(time_layout)
    
    def paintEvent(self, event):
        """绘制卡片背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取组件矩形，但留出一些边距
        rect = self.rect().adjusted(4, 4, -4, -4)
        
        # 设置背景色
        if self.is_hovered:
            background_color = QColor("#fafafa")
            border_color = QColor(self.color)
        else:
            background_color = QColor("#ffffff")
            border_color = QColor("#e8e8e8")
        
        # 绘制背景
        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, 12, 12)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.is_hovered = True
        self.update()  # 触发重绘
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.is_hovered = False
        self.update()  # 触发重绘
        super().leaveEvent(event)

    def _lighten_color(self, color):
        """使颜色变亮"""
        if color.startswith('#'):
            color = color[1:]
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # 增加亮度
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_description_display(self):
        """更新描述显示"""
        self.setToolTip(self.description.strip())
    
    def update_display(self):
        """更新显示内容"""
        now = datetime.now()
        
        if now >= self.target_time:
            # 倒计时结束
            self.time_label.setText("时间到!")
            self.time_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: bold;
                    color: #ff5722;
                    background: transparent;
                }
            """)
            self.progress_bar.setValue(100)
            return
        
        # 计算剩余时间
        remaining = self.target_time - now
        total_seconds = int(remaining.total_seconds())
        
        # 格式化时间显示（只显示天数）
        if total_seconds > 86400:  # 超过1天
            days = total_seconds // 86400
            time_text = f"{days}天"
        else:  # 不足1天
            time_text = "最后1天"
            
        self.time_label.setText(time_text)
        
        # 更新进度条 - 显示已完成时间百分比
        if now <= self.start_time:
            # 还没到开始时间
            progress = 0
        elif now >= self.target_time:
            # 已经超过目标时间
            progress = 100
        else:
            # 正常情况：计算已过时间百分比
            total_duration = (self.target_time - self.start_time).total_seconds()
            elapsed = (now - self.start_time).total_seconds()
            if total_duration > 0:
                progress = max(0, min(100, int((elapsed / total_duration) * 100)))
            else:
                progress = 100  # 如果持续时间为0，显示100%
        
        self.progress_bar.setValue(progress)
        
        # 更新目标时间显示
        self.target_label.setText(f"目标: {self.target_time.strftime('%Y-%m-%d')}")
    
    def edit_countdown(self):
        """编辑倒计时"""
        dialog = CountdownEditDialog(self.title, self.start_time, self.target_time, self.description, self.color)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            
            self.title = data['title']
            self.start_time = data['start_time']
            self.target_time = data['target_time']
            self.description = data['description']
            self.color = data['color']
            
            # 更新UI
            self.title_label.setText(self.title)
            
            # 更新描述标签
            self.update_description_display()
            
            # 立即更新显示内容
            self.update_display()
            
            # 强制重绘组件以确保显示更新
            self.update()
            self.repaint()
            
            # 确保定时器正常工作
            if not self.timer.isActive():
                self.timer.start(1000)
            
            # 触发重绘以更新颜色
            self.update()
            
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 3px;
                    background-color: rgba(0, 0, 0, 0.05);
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    border-radius: 3px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.color}, stop:0.5 {self._lighten_color(self.color)}, stop:1 {self.color});
                }}
            """)
            
            self.time_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: 600;
                    color: {self.color};
                    background: transparent;
                    padding: 1px 0px;
                }}
            """)
            
            # 发射编辑信号
            self.item_edited.emit(self.countdown_id, data)
    
    def delete_countdown(self):
        """删除倒计时"""
        reply = QtWidgets.QMessageBox.question(
            None, '确认删除',
            f'确定要删除倒计时 "{self.title}" 吗？',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.timer.stop()  # 停止定时器
            self.item_deleted.emit(self.countdown_id)


class CountdownEditDialog(QtWidgets.QDialog):
    """倒计时编辑对话框"""
    
    def __init__(self, title='', start_time=None, target_time=None, description='', color='#4CAF50', parent=None):
        super().__init__(parent)
        self.start_time = start_time or datetime.now()
        self.target_time = target_time or datetime.now() + timedelta(days=1)
        self.setup_ui()
        
        # 设置初始值
        self.title_edit.setText(title)
        self.description_edit.setText(description)
        self.start_date_edit.setDate(self.start_time.date())
        self.target_date_edit.setDate(self.target_time.date())
        
        # 添加时间验证
        self.start_date_edit.dateChanged.connect(self.validate_time_range)
        self.target_date_edit.dateChanged.connect(self.validate_time_range)
        
        # 设置颜色（在setup_ui之后）
        if color in self.colors:
            self.set_color(color)
        else:
            self.set_color(self.colors[0])  # 使用默认颜色
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle('编辑倒计时')
        self.setFixedSize(350, 400)  # 调整高度
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 12px;
                color: #333;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #4CAF50;
            }
            QDateEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 30px 8px 8px;
                font-size: 12px;
                background-color: white;
            }
            QDateEdit:focus {
                border-color: #4CAF50;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border: none;
                background-color: #f8f8f8;
                border-left: 1px solid #ddd;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QDateEdit::drop-down:hover {
                background-color: #e8e8e8;
            }
            QDateEdit::drop-down:pressed {
                background-color: #d8d8d8;
            }
            QDateEdit::down-arrow {
                image: none;
                border: 2px solid #666;
                border-top: none;
                border-left: none;
                width: 6px;
                height: 6px;
                transform: rotate(45deg);
                margin-bottom: 2px;
            }
            QDateEdit::down-arrow:hover {
                border-color: #333;
            }
            QCalendarWidget {
                background-color: white;
                gridline-color: #e0e0e0;
                font-size: 12px;
            }
            QCalendarWidget QWidget {
                background-color: white;
                color: #333;
            }
            QCalendarWidget QTableView {
                background-color: white;
                alternate-background-color: #f5f5f5;
                selection-background-color: #4CAF50;
                selection-color: white;
                gridline-color: #e0e0e0;
            }
            QCalendarWidget QHeaderView::section {
                background-color: #f0f0f0;
                color: #333;
                padding: 4px;
                font-weight: bold;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: #333;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                color: #333;
            }
            QCalendarWidget QToolButton {
                background-color: white;
                color: #333;
                border-radius: 2px;
                margin: 1px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #f0f0f0;
            }
            QCalendarWidget QToolButton:pressed {
                background-color: #e0e0e0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题
        layout.addWidget(QtWidgets.QLabel('标题:'))
        self.title_edit = QtWidgets.QLineEdit()
        self.title_edit.setPlaceholderText('输入倒计时标题')
        layout.addWidget(self.title_edit)
        
        # 开始时间
        layout.addWidget(QtWidgets.QLabel('开始时间:'))
        self.start_date_edit = QtWidgets.QDateEdit()
        self.start_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(datetime.now().date())
        layout.addWidget(self.start_date_edit)
        
        # 目标时间
        layout.addWidget(QtWidgets.QLabel('目标时间:'))
        self.target_date_edit = QtWidgets.QDateEdit()
        self.target_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.setMinimumDate(datetime.now().date())
        layout.addWidget(self.target_date_edit)
        
        # 描述
        layout.addWidget(QtWidgets.QLabel('描述 (可选):'))
        self.description_edit = QtWidgets.QTextEdit()
        self.description_edit.setFixedHeight(50)
        self.description_edit.setPlaceholderText('输入描述信息')
        layout.addWidget(self.description_edit)
        
        # 颜色选择
        layout.addWidget(QtWidgets.QLabel('颜色:'))
        color_layout = QtWidgets.QHBoxLayout()

        self.color_buttons = []
        self.colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#795548']
        
        for i, color in enumerate(self.colors):
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid transparent;
                    border-radius: 15px;
                }}
                QPushButton:checked {{
                    border-color: #333;
                }}
            """)
            btn.setCheckable(True)
            # 修复lambda闭包问题：使用partial或者直接在函数中处理
            btn.color = color  # 将颜色存储在按钮对象上
            btn.clicked.connect(self.on_color_button_clicked)
            self.color_buttons.append(btn)
            color_layout.addWidget(btn)
        
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        layout.addStretch()
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QtWidgets.QPushButton('取消')
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ccc;
                color: #333;
            }
            QPushButton:hover {
                background-color: #bbb;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QtWidgets.QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # 默认选择第一个颜色
        self.selected_color = self.colors[0]
        if self.color_buttons:
            self.color_buttons[0].setChecked(True)
    
    def on_color_button_clicked(self):
        """处理颜色按钮点击"""
        sender = self.sender()
        if hasattr(sender, 'color'):
            self.set_color(sender.color)
    
    def set_color(self, color):
        """设置选中的颜色"""
        self.selected_color = color
        for btn in self.color_buttons:
            btn.setChecked(False)
        
        # 找到对应颜色的按钮并选中
        if color in self.colors:
            idx = self.colors.index(color)
            self.color_buttons[idx].setChecked(True)
    
    def validate_time_range(self):
        """验证时间范围：开始时间必须早于目标时间"""
        start_date = self.start_date_edit.date().toPython()
        target_date = self.target_date_edit.date().toPython()
        
        if start_date >= target_date:
            # 如果开始时间不早于目标时间，自动调整目标时间
            new_target = start_date + timedelta(days=1)  # 默认增加1天
            self.target_date_edit.setDate(new_target)
            
            # 显示提示
            self.setWindowTitle('编辑倒计时 - 时间已自动调整')
        else:
            self.setWindowTitle('编辑倒计时')
    
    def get_data(self):
        """获取对话框数据"""
        # 将日期转换为datetime对象
        start_date = self.start_date_edit.date().toPython()
        target_date = self.target_date_edit.date().toPython()
        
        return {
            'title': self.title_edit.text().strip() or '倒计时',
            'start_time': datetime.combine(start_date, datetime.min.time()),  # 开始时间：当天00:00:00
            'target_time': datetime.combine(target_date, datetime.max.time().replace(microsecond=0)),  # 结束时间：当天23:59:59
            'description': self.description_edit.toPlainText().strip(),
            'color': getattr(self, 'selected_color', self.colors[0])  # 确保有默认颜色
        }


class CountdownCard(SidebarWidget):
    """倒计时卡片组件"""
    
    name = '倒计时'
    category = '时间'
    icon = 'mdi.account-clock-outline'
    description = '创建和管理倒计时，支持进度条显示和多项目管理'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.countdowns = {}  # 存储倒计时数据
        self.countdown_widgets = {}  # 存储倒计时组件
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        self.resize(300, 400)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 头部
        header = QtWidgets.QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px 8px 0 0;
            }
        """)
        
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # 标题
        title_label = QtWidgets.QLabel('倒计时')
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 添加按钮
        add_btn = QtWidgets.QPushButton()
        add_btn.setIcon(qtawesome.icon('fa5s.plus', color='white'))
        add_btn.setFixedSize(30, 30)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        add_btn.clicked.connect(self.add_countdown)
        header_layout.addWidget(add_btn)
        
        main_layout.addWidget(header)
        
        # 内容区域
        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 0 0 8px 8px;
            }
        """)
        
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(0)
        
        # 滚动区域
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        # 倒计时列表容器
        self.countdown_container = QtWidgets.QWidget()
        self.countdown_container.setStyleSheet("QWidget { background-color: transparent; }")
        self.countdown_layout = QtWidgets.QVBoxLayout(self.countdown_container)
        self.countdown_layout.setContentsMargins(0, 8, 0, 8)
        self.countdown_layout.setSpacing(4)
        self.countdown_layout.addStretch()
        
        scroll_area.setWidget(self.countdown_container)
        content_layout.addWidget(scroll_area)
        
        main_layout.addWidget(content_widget, 1)
        
        # 空状态提示
        self.empty_label = QtWidgets.QLabel('还没有倒计时项目\n点击 + 添加第一个')
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
                background: transparent;
                padding: 40px;
            }
        """)
        self.countdown_layout.insertWidget(0, self.empty_label)
        
    def add_countdown(self):
        """添加倒计时"""
        dialog = CountdownEditDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            countdown_id = str(uuid.uuid4())
            
            # 存储数据（start_time已经在对话框中设置）
            self.countdowns[countdown_id] = data
            
            # 创建组件
            widget = CountdownItemWidget(countdown_id, data, self.countdown_container)
            widget.item_deleted.connect(self.delete_countdown)
            widget.item_edited.connect(self.edit_countdown)
            
            # 添加到布局
            self.countdown_layout.insertWidget(self.countdown_layout.count() - 1, widget)
            self.countdown_widgets[countdown_id] = widget
            
            # 隐藏空状态
            self.empty_label.hide()
            
            # 保存配置
            self.save_config_signal.emit()
    
    def delete_countdown(self, countdown_id):
        """删除倒计时"""
        if countdown_id in self.countdown_widgets:
            widget = self.countdown_widgets[countdown_id]
            self.countdown_layout.removeWidget(widget)
            widget.deleteLater()
            
            del self.countdown_widgets[countdown_id]
            del self.countdowns[countdown_id]
            
            # 如果没有倒计时了，显示空状态
            if not self.countdowns:
                self.empty_label.show()
            
            # 保存配置
            self.save_config_signal.emit()
    
    def edit_countdown(self, countdown_id, data):
        """编辑倒计时"""
        if countdown_id in self.countdowns:
            self.countdowns[countdown_id] = data
            self.save_config_signal.emit()
    
    def get_config(self):
        """获取配置"""
        # 将datetime对象转换为ISO字符串进行序列化
        config_data = {}
        for countdown_id, data in self.countdowns.items():
            config_data[countdown_id] = {
                'title': data['title'],
                'target_time': data['target_time'].isoformat(),
                'description': data['description'],
                'color': data['color'],
                'start_time': data.get('start_time', data.get('create_time', datetime.now())).isoformat()
            }
        return {'countdowns': config_data}
    
    def set_config(self, config):
        """设置配置"""
        countdown_data = config.get('countdowns', {})
        
        # 清空现有数据
        for widget in list(self.countdown_widgets.values()):
            if hasattr(widget, 'timer'):
                widget.timer.stop()
            widget.deleteLater()
        
        self.countdown_widgets.clear()
        self.countdowns.clear()
        
        # 加载数据
        for countdown_id, data in countdown_data.items():
            # 将ISO字符串转换回datetime对象
            data['target_time'] = datetime.fromisoformat(data['target_time'])
            
            # 处理开始时间（向后兼容旧配置）
            if 'start_time' in data:
                data['start_time'] = datetime.fromisoformat(data['start_time'])
            elif 'create_time' in data:
                # 向后兼容：如果有create_time但没有start_time，使用create_time
                data['start_time'] = datetime.fromisoformat(data['create_time'])
            else:
                # 如果都没有，使用当前时间（向后兼容）
                data['start_time'] = datetime.now()
            
            self.countdowns[countdown_id] = data
            
            # 创建组件
            widget = CountdownItemWidget(countdown_id, data, self.countdown_container)
            widget.item_deleted.connect(self.delete_countdown)
            widget.item_edited.connect(self.edit_countdown)
            
            # 添加到布局
            self.countdown_layout.insertWidget(self.countdown_layout.count() - 1, widget)
            self.countdown_widgets[countdown_id] = widget
        
        # 更新空状态显示
        if self.countdowns:
            self.empty_label.hide()
        else:
            self.empty_label.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = CountdownCard()
    widget.show()
    app.exec_()
