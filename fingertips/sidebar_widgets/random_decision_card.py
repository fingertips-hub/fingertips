import random
import math
from datetime import datetime
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide2.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QPolygon
from PySide2.QtWidgets import QSizePolicy
import qtawesome
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget


class DecisionScrollWidget(QtWidgets.QWidget):
    """决策滚动列表组件"""
    
    # 信号定义
    selection_finished = QtCore.Signal(str)  # 选择完成信号
    
    def __init__(self, options=None, parent=None):
        super().__init__(parent)
        self.options = options or ["选项1", "选项2", "选项3", "选项4"]
        self.current_offset = 0  # 当前滚动偏移量
        self.target_offset = 0   # 目标滚动偏移量
        self.is_scrolling = False
        self.item_height = 50    # 每个选项的高度
        self.selected_index = 0  # 当前选中的选项索引
        
        # 动画
        self.animation = QPropertyAnimation(self, b"scroll_offset")
        self.animation.setDuration(3000)  # 3秒动画
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self.on_animation_finished)
        
        # 颜色调色板
        self.colors = [
            QColor(255, 107, 107),  # 红色
            QColor(78, 205, 196),   # 青色
            QColor(255, 165, 0),    # 橙色
            QColor(106, 137, 204),  # 蓝色
            QColor(255, 193, 7),    # 黄色
            QColor(220, 20, 60),    # 深红
            QColor(50, 205, 50),    # 绿色
            QColor(138, 43, 226),   # 紫色
        ]
        
        self.setMinimumSize(250, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def set_options(self, options):
        """设置选项"""
        self.options = options or ["暂无选项"]
        # 重置滚动位置
        self.current_offset = 0
        self.target_offset = 0
        self.selected_index = 0
        # 强制重绘
        self.update()
        
    def start_spin(self):
        """开始滚动选择"""
        if self.is_scrolling or not self.options:
            return
            
        self.is_scrolling = True
        
        # 重新初始化随机种子，确保真正的随机性
        import time
        random.seed(int(time.time() * 1000000) % 2147483647)
        
        # 计算随机滚动距离（在当前位置基础上增加）
        # 增加更多随机性，避免重复出现相同结果
        
        # 基础轮数：5-12轮，范围更大
        base_rounds = random.randint(5, 12)
        
        # 额外随机偏移：不只是选项数量，而是更大的随机范围
        extra_offset = random.randint(0, len(self.options) * 2 - 1)
        
        # 添加一个完全随机的额外滚动量，增加不可预测性
        random_boost = random.randint(0, len(self.options) // 2 + 2)
        
        # 总的额外滚动距离
        total_additional = base_rounds * len(self.options) + extra_offset + random_boost
        
        # 目标位置 = 当前位置 + 额外滚动距离
        self.target_offset = self.current_offset + total_additional * self.item_height
        
        # 随机化动画时间，增加不可预测性
        animation_duration = random.randint(2500, 3500)  # 2.5-3.5秒
        self.animation.setDuration(animation_duration)
        
        # 开始动画
        self.animation.setStartValue(self.current_offset)
        self.animation.setEndValue(self.target_offset)
        self.animation.start()
        
    def on_animation_finished(self):
        """动画完成"""
        self.is_scrolling = False
        
        # 根据最终滚动位置计算实际选中的选项
        selected_option = self.get_selected_option()
        if selected_option:
            self.selection_finished.emit(selected_option)
            
    def get_selected_option(self):
        """获取当前中间位置选中的选项"""
        if not self.options:
            return None
            
        # 获取绘制区域
        rect = self.rect()
        center_y = rect.height() // 2
        selection_offset = -20  # 向上偏移20px，与绘制逻辑保持一致
        # 箭头实际指向的Y坐标
        arrow_y = center_y + selection_offset
        
        # 计算当前滚动位置下的绘制参数（与paintEvent中的逻辑完全一致）
        start_offset = self.current_offset % (len(self.options) * self.item_height)
        start_item = int(start_offset // self.item_height)
        pixel_offset = start_offset % self.item_height
        
        # 创建重复的选项列表用于滚动显示
        visible_items = rect.height() // self.item_height + 2
        extended_options = self.options * (visible_items // len(self.options) + 3)
        
        # 找到箭头指向位置最接近的选项
        closest_distance = float('inf')
        selected_option = None
        in_selection_area = False
        
        for i in range(visible_items + 1):
            # 计算选项位置（与paintEvent中完全一致）
            y_pos = i * self.item_height - pixel_offset
            
            # 如果选项不在可见区域内，跳过
            if y_pos + self.item_height < 0 or y_pos > rect.height():
                continue
                
            # 计算距离箭头位置的距离
            item_center = y_pos + self.item_height // 2
            distance_from_arrow = abs(item_center - arrow_y)
            
            # 计算实际的选项索引
            actual_option_index = (start_item + i) % len(self.options)
            
            # 判断是否在选中区域内（基于箭头位置）
            selection_area_top = arrow_y - self.item_height // 2
            selection_area_bottom = arrow_y + self.item_height // 2
            
            # 判断item是否与选中区域有重叠
            item_top = y_pos
            item_bottom = y_pos + self.item_height
            
            is_in_selection = not (item_bottom <= selection_area_top or item_top >= selection_area_bottom)
            
            if is_in_selection:
                # 在选中区域内，优先选择最接近箭头的
                if not in_selection_area or distance_from_arrow < closest_distance:
                    closest_distance = distance_from_arrow
                    selected_option = self.options[actual_option_index]
                    in_selection_area = True
            elif not in_selection_area:
                # 不在选中区域内，且还没有找到在选中区域内的选项
                if distance_from_arrow < closest_distance:
                    closest_distance = distance_from_arrow
                    selected_option = self.options[actual_option_index]
        
        return selected_option
            
    @QtCore.Property(float)
    def scroll_offset(self):
        return self.current_offset
        
    @scroll_offset.setter
    def scroll_offset(self, offset):
        self.current_offset = offset
        self.update()
        
    def paintEvent(self, event):
        """绘制滚动列表"""
        if not self.options:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # 获取绘制区域
        rect = self.rect()
        center_y = rect.height() // 2
        
        # 绘制背景
        painter.fillRect(rect, QColor(248, 249, 250))
        
        # 调整选中区域位置，让箭头指向选中项的中心
        # 选中区域向上偏移14px，优化箭头对准选项的位置
        selection_offset = -20  # 向上偏移20px
        select_rect = QtCore.QRect(0, center_y - self.item_height // 2 + selection_offset, rect.width(), self.item_height)
        painter.fillRect(select_rect, QColor(220, 220, 220, 100))
        
        # 绘制选中区域边框
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(select_rect)
        
        # 计算当前应该显示的选项
        visible_items = rect.height() // self.item_height + 2  # 多绘制一些以避免空白
        
        # 创建重复的选项列表用于滚动显示
        extended_options = self.options * (visible_items // len(self.options) + 3)
        
        # 计算起始绘制位置
        start_offset = self.current_offset % (len(self.options) * self.item_height)
        start_item = int(start_offset // self.item_height)
        pixel_offset = start_offset % self.item_height
        
        # 绘制选项
        for i in range(visible_items + 1):
            item_index = (start_item + i) % len(extended_options)
            option = extended_options[item_index]
            
            # 计算选项位置
            y_pos = i * self.item_height - pixel_offset
            item_rect = QtCore.QRect(0, y_pos, rect.width(), self.item_height)
            
            # 如果选项不在可见区域内，跳过
            if y_pos + self.item_height < 0 or y_pos > rect.height():
                continue
                
            # 计算距离中心的距离，用于缩放效果
            item_center = y_pos + self.item_height // 2
            distance_from_center = abs(item_center - center_y)
            max_distance = rect.height() // 2
            
            # 计算缩放比例 (距离中心越近越大)
            if distance_from_center <= self.item_height // 2:
                # 在选中区域内，最大缩放
                scale = 1.3
                alpha = 255
            else:
                # 根据距离计算缩放比例
                scale = max(0.6, 1.3 - (distance_from_center - self.item_height // 2) / max_distance * 0.7)
                alpha = max(100, int(255 - (distance_from_center / max_distance) * 155))
            
            # 选择颜色
            color_index = (start_item + i) % len(self.options)
            color = self.colors[color_index % len(self.colors)]
            color.setAlpha(alpha)
            
            # 绘制选项背景
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.white, 1))
            
            # 缩放后的矩形
            scaled_width = int(rect.width() * 0.9)  # 稍微缩小宽度
            scaled_height = int(self.item_height * scale)
            scaled_x = (rect.width() - scaled_width) // 2
            scaled_y = item_center - scaled_height // 2
            
            scaled_rect = QtCore.QRect(scaled_x, scaled_y, scaled_width, scaled_height)
            painter.drawRoundedRect(scaled_rect, 8, 8)
            
            # 绘制文字
            painter.setPen(QPen(Qt.white))
            font_size = int(12 * scale)
            font = QFont("Microsoft YaHei", font_size, QFont.Bold)
            painter.setFont(font)
            
            # 限制文字长度
            display_text = option
            if len(option) > 8:
                display_text = option[:7] + "..."
                
            painter.drawText(scaled_rect, Qt.AlignCenter, display_text)
        
        # 绘制指示箭头（与选中区域中心对齐）
        painter.setPen(QPen(QColor(255, 0, 0), 3))
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        
        # 箭头位置与选中区域中心对齐
        arrow_y = center_y + selection_offset
        
        # 左箭头
        left_arrow = QPolygon([
            QtCore.QPoint(10, arrow_y),
            QtCore.QPoint(25, arrow_y - 10),
            QtCore.QPoint(25, arrow_y + 10)
        ])
        painter.drawPolygon(left_arrow)
        
        # 右箭头
        right_arrow = QPolygon([
            QtCore.QPoint(rect.width() - 10, arrow_y),
            QtCore.QPoint(rect.width() - 25, arrow_y - 10),
            QtCore.QPoint(rect.width() - 25, arrow_y + 10)
        ])
        painter.drawPolygon(right_arrow)


class HistoryItemWidget(QtWidgets.QWidget):
    """历史记录项组件"""
    
    # 信号定义
    delete_requested = QtCore.Signal()
    
    def __init__(self, result, timestamp, parent=None):
        super().__init__(parent)
        self.result = result
        self.timestamp = timestamp
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setFixedHeight(35)
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 6px;
                border: 1px solid #e9ecef;
            }
            QWidget:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # 结果文本
        result_label = QtWidgets.QLabel(self.result)
        result_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(result_label, 1)
        
        # 时间戳
        time_str = self.timestamp.strftime("%H:%M")
        time_label = QtWidgets.QLabel(time_str)
        time_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 10px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(time_label)
        
        # 删除按钮
        delete_btn = QtWidgets.QPushButton()
        delete_btn.setIcon(qtawesome.icon('fa.times', color='#999'))
        delete_btn.setFixedSize(20, 20)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 10px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #dc3545;
            }
            QPushButton:hover {
                icon: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTkgM0wzIDkiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPHBhdGggZD0iTTMgM0w5IDkiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+);
            }
        """)
        delete_btn.clicked.connect(self.delete_requested.emit)
        layout.addWidget(delete_btn)


class OptionsEditDialog(QtWidgets.QDialog):
    """选项编辑对话框"""
    
    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.options = options.copy()
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("编辑选项")
        self.setFixedSize(350, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 12px;
                color: #333;
            }
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QtWidgets.QLabel("管理决策选项")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)
        
        # 新增选项
        add_layout = QtWidgets.QHBoxLayout()
        add_layout.setSpacing(8)
        
        self.new_option_input = QtWidgets.QLineEdit()
        self.new_option_input.setPlaceholderText("输入新选项...")
        self.new_option_input.returnPressed.connect(self.add_option)
        add_layout.addWidget(self.new_option_input, 1)
        
        add_btn = QtWidgets.QPushButton("添加")
        add_btn.clicked.connect(self.add_option)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # 选项列表
        list_label = QtWidgets.QLabel("当前选项:")
        layout.addWidget(list_label)
        
        # 滚动区域
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        self.options_container = QtWidgets.QWidget()
        self.options_layout = QtWidgets.QVBoxLayout(self.options_container)
        self.options_layout.setContentsMargins(8, 8, 8, 8)
        self.options_layout.setSpacing(6)
        
        scroll_area.setWidget(self.options_container)
        layout.addWidget(scroll_area, 1)
        
        # 按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QtWidgets.QPushButton("取消")
        cancel_btn.setStyleSheet("background-color: #6c757d;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QtWidgets.QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # 加载现有选项
        self.refresh_options_list()
        
    def add_option(self):
        """添加选项"""
        text = self.new_option_input.text().strip()
        if text and text not in self.options:
            self.options.append(text)
            self.new_option_input.clear()
            self.refresh_options_list()
            
    def remove_option(self, option):
        """删除选项"""
        if option in self.options and len(self.options) > 2:  # 至少保留2个选项
            self.options.remove(option)
            self.refresh_options_list()
            
    def refresh_options_list(self):
        """刷新选项列表"""
        # 清除现有组件
        for i in reversed(range(self.options_layout.count())):
            item = self.options_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                self.options_layout.removeItem(item)
                
        # 添加选项组件
        for option in self.options:
            option_widget = QtWidgets.QWidget()
            option_layout = QtWidgets.QHBoxLayout(option_widget)
            option_layout.setContentsMargins(6, 4, 6, 4)
            option_layout.setSpacing(8)
            
            option_label = QtWidgets.QLabel(option)
            option_label.setStyleSheet("background: transparent; border: none;")
            option_layout.addWidget(option_label, 1)
            
            delete_btn = QtWidgets.QPushButton()
            delete_btn.setIcon(qtawesome.icon('fa.trash', color='#dc3545'))
            delete_btn.setFixedSize(24, 24)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #dc3545;
                }
            """)
            delete_btn.clicked.connect(lambda checked=None, opt=option: self.remove_option(opt))
            option_layout.addWidget(delete_btn)
            
            self.options_layout.addWidget(option_widget)
            
        # 添加弹性空间
        self.options_layout.addStretch()
        
    def get_options(self):
        """获取选项列表"""
        return self.options


class RandomDecisionCard(SidebarWidget):
    """随机决策器组件"""
    
    name = '随机决策器'
    category = '生活'
    icon = 'fa.random'
    description = '帮助你做选择的小工具，支持自定义选项和滚动选择效果'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据
        self.options = ["去看电影", "在家休息", "出去吃饭", "运动健身"]
        self.history = []  # 历史记录
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        self.setMinimumSize(300, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: none;
            }
        """)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(6)
        
        # 头部
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(10)
        
        # 标题
        title_label = QtWidgets.QLabel("随机决策器")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 编辑选项按钮
        edit_btn = QtWidgets.QPushButton()
        edit_btn.setIcon(qtawesome.icon('fa.cog', color='#666'))
        edit_btn.setFixedSize(32, 32)
        edit_btn.setToolTip("编辑选项")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        edit_btn.clicked.connect(self.edit_options)
        header_layout.addWidget(edit_btn)
        
        main_layout.addLayout(header_layout)
        
        # 滚动选择区域
        scroll_container = QtWidgets.QWidget()
        scroll_container.setFixedHeight(220)
        scroll_layout = QtWidgets.QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(0, 10, 0, 10)
        
        self.decision_scroll = DecisionScrollWidget(self.options)
        self.decision_scroll.selection_finished.connect(self.on_selection_finished)
        scroll_layout.addWidget(self.decision_scroll)
        
        main_layout.addWidget(scroll_container)
        
        # 控制按钮
        self.spin_button = QtWidgets.QPushButton("开始决策")
        self.spin_button.setFixedHeight(40)
        self.spin_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.spin_button.clicked.connect(self.start_decision)
        main_layout.addWidget(self.spin_button)
        
        # 结果显示
        self.result_label = QtWidgets.QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            QLabel {
                color: #007bff;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                padding: 8px;
                border: 2px solid #007bff;
                border-radius: 8px;
            }
        """)
        self.result_label.hide()
        main_layout.addWidget(self.result_label)
        
        # 历史记录
        history_layout = QtWidgets.QVBoxLayout()
        history_layout.setSpacing(8)
        
        history_header_layout = QtWidgets.QHBoxLayout()
        history_title = QtWidgets.QLabel("历史记录")
        history_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                background: transparent;
            }
        """)
        history_header_layout.addWidget(history_title)
        
        history_header_layout.addStretch()
        
        # 清空历史按钮
        clear_history_btn = QtWidgets.QPushButton()
        clear_history_btn.setIcon(qtawesome.icon('fa.trash', color='#999'))
        clear_history_btn.setFixedSize(24, 24)
        clear_history_btn.setToolTip("清空历史")
        clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        clear_history_btn.clicked.connect(self.clear_history)
        history_header_layout.addWidget(clear_history_btn)
        
        history_layout.addLayout(history_header_layout)
        
        # 历史记录滚动区域
        self.history_scroll = QtWidgets.QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setMaximumHeight(120)
        self.history_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
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
        
        self.history_container = QtWidgets.QWidget()
        self.history_layout = QtWidgets.QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(6, 6, 6, 6)
        self.history_layout.setSpacing(4)
        self.history_layout.addStretch()
        
        self.history_scroll.setWidget(self.history_container)
        history_layout.addWidget(self.history_scroll)
        
        main_layout.addLayout(history_layout)
        
    def start_decision(self):
        """开始决策"""
        if len(self.options) < 2:
            # 使用合适的父窗口
            dialog_parent = self.get_dialog_parent()
            QtWidgets.QMessageBox.warning(dialog_parent, "提示", "至少需要2个选项才能开始决策")
            return
            
        self.spin_button.setEnabled(False)
        self.spin_button.setText("决策中...")
        self.result_label.hide()
        self.decision_scroll.start_spin()
        
    def on_selection_finished(self, result):
        """决策完成"""
        self.spin_button.setEnabled(True)
        self.spin_button.setText("开始决策")
        
        # 显示结果
        self.result_label.setText(f"🎯 结果: {result}")
        self.result_label.show()
        
        # 添加到历史记录
        self.add_to_history(result)
        
    def add_to_history(self, result):
        """添加到历史记录"""
        timestamp = datetime.now()
        self.history.insert(0, {"result": result, "timestamp": timestamp})
        
        # 限制历史记录数量
        if len(self.history) > 10:
            self.history = self.history[:10]
            
        self.refresh_history_display()
        
    def refresh_history_display(self):
        """刷新历史记录显示"""
        # 清除现有历史记录组件
        for i in reversed(range(self.history_layout.count() - 1)):  # 保留最后的stretch
            item = self.history_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                self.history_layout.removeItem(item)
                
        # 添加历史记录组件
        for i, record in enumerate(self.history):
            history_item = HistoryItemWidget(
                record["result"], 
                record["timestamp"]
            )
            history_item.delete_requested.connect(lambda idx=i: self.remove_history_item(idx))
            self.history_layout.insertWidget(i, history_item)
            
    def remove_history_item(self, index):
        """删除历史记录项"""
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self.refresh_history_display()
            
    def clear_history(self):
        """清空历史记录"""
        if self.history:
            # 使用合适的父窗口
            dialog_parent = self.get_dialog_parent()
            reply = QtWidgets.QMessageBox.question(
                dialog_parent, "确认", "确定要清空所有历史记录吗？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.history.clear()
                self.refresh_history_display()
                
    def edit_options(self):
        """编辑选项"""
        # 使用合适的父窗口，解决dialog显示和程序退出问题
        dialog_parent = self.get_dialog_parent()
        dialog = OptionsEditDialog(self.options, dialog_parent)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_options = dialog.get_options()
            if len(new_options) >= 2:
                self.options = new_options
                self.decision_scroll.set_options(self.options)
                self.save_config_signal.emit()
            else:
                # 使用合适的父窗口
                dialog_parent = self.get_dialog_parent()
                QtWidgets.QMessageBox.warning(dialog_parent, "提示", "至少需要2个选项")
                
    def get_config(self):
        """获取配置"""
        return {
            "options": self.options,
            "history": [
                {
                    "result": record["result"],
                    "timestamp": record["timestamp"].isoformat()
                }
                for record in self.history
            ]
        }
        
    def set_config(self, config):
        """设置配置"""
        if not isinstance(config, dict):
            return
            
        # 加载选项
        self.options = config.get("options", self.options)
        self.decision_scroll.set_options(self.options)
        
        # 加载历史记录
        history_data = config.get("history", [])
        self.history = []
        for record in history_data:
            try:
                timestamp = datetime.fromisoformat(record["timestamp"])
                self.history.append({
                    "result": record["result"],
                    "timestamp": timestamp
                })
            except (KeyError, ValueError):
                continue
                
        self.refresh_history_display() 