import sys
import uuid

from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout,  QPushButton, QHBoxLayout, QGraphicsOpacityEffect
from PySide2.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QObject, QEasingCurve, \
    QPoint, QSize
from PySide2.QtGui import QCursor, QColor, QPainter, QBrush, QLinearGradient, QIcon
import qtawesome
import qfluentwidgets
from qfluentwidgets.common.animation import TranslateYAnimation

from fingertips.super_sidebar.acrylic_style import WindowEffect
from fingertips.super_sidebar.layout import ContentView
from fingertips.settings.config_model import config_model
from fingertips.super_sidebar.sidebar_widget_utils import discover_sidebar_widgets


class MenuButton(QPushButton):
    """ 菜单按钮 """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._menu = None
        self.arrow_ani = TranslateYAnimation(self)

    def set_menu(self, menu):
        self._menu = menu

    def menu(self):
        return self._menu

    def _show_menu(self):
        if not self.menu():
            return

        menu = self.menu()
        menu.view.setMinimumWidth(self.width())
        menu.view.adjustSize()
        menu.adjustSize()

        # determine the animation type by choosing the maximum height of view
        x = -menu.width()//2 + menu.layout().contentsMargins().left() + self.width()//2
        pd = self.mapToGlobal(QPoint(x, self.height()))
        hd = menu.view.heightForAnimation(pd, qfluentwidgets.MenuAnimationType.DROP_DOWN)

        pu = self.mapToGlobal(QPoint(x, 0))
        hu = menu.view.heightForAnimation(pu, qfluentwidgets.MenuAnimationType.PULL_UP)

        if hd >= hu:
            menu.view.adjustSize(pd, qfluentwidgets.MenuAnimationType.DROP_DOWN)
            menu.exec(pd, aniType=qfluentwidgets.MenuAnimationType.DROP_DOWN)
        else:
            menu.view.adjustSize(pu, qfluentwidgets.MenuAnimationType.PULL_UP)
            menu.exec(pu, aniType=qfluentwidgets.MenuAnimationType.PULL_UP)

    def _hide_menu(self):
        if self.menu():
            self.menu().hide()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._show_menu()


class SuperSidebar(QMainWindow):
    # 位置常量
    LEFT = "left"
    RIGHT = "right"
    
    # 宽度限制常量
    MIN_WIDTH = 300
    MAX_WIDTH = 1000
    RESIZE_BORDER_WIDTH = 10  # 可拖拽边缘的宽度

    def __init__(self, position=RIGHT, panel_width=600, opacity=0.7, enable_aero=True):
        """
        初始化侧边栏

        参数:
            position: 侧边栏位置，可以是 SiderBar.LEFT 或 SiderBar.RIGHT
            opacity: 背景透明度，0.0-1.0的浮点数，0为完全透明，1为完全不透明
        """
        super().__init__()

        self._widget_menu = qfluentwidgets.RoundMenu(parent=self)

        # 保存位置设置
        self.position = position
        if self.position not in [self.LEFT, self.RIGHT]:
            self.position = self.RIGHT  # 默认为右侧

        # 设置透明度
        self.opacity = max(0.0, min(1.0, opacity))  # 确保在0-1范围内
        self.enable_aero = enable_aero

        # 设置窗口标志，无边框和置顶
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 避免窗口激活导致的闪烁
        
        # 根据是否启用亚克力效果来设置不同的透明属性
        if enable_aero:
            # 亚克力效果时不使用 WA_TranslucentBackground，防止点击穿透
            self.setAttribute(Qt.WA_NoSystemBackground)
        else:
            # 非亚克力效果时使用透明背景
            self.setAttribute(Qt.WA_TranslucentBackground)

        # 获取所有屏幕信息
        self.update_screen_info()

        # 设置窗口尺寸 - 从配置中读取宽度设置，确保在有效范围内
        self.panel_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, config_model.super_sidebar_width.value))

        if self.position == self.LEFT:
            self.setFixedSize(self.panel_width, self.leftmost_screen_height)
            # 初始位置放在最左侧屏幕的左边界外
            self.setGeometry(self.leftmost_screen_left - self.panel_width,
                             self.leftmost_screen_top,
                             self.panel_width,
                             self.leftmost_screen_height)
        else:  # RIGHT
            self.setFixedSize(self.panel_width, self.rightmost_screen_height)
            # 初始位置放在最右侧屏幕的右边界外
            self.setGeometry(self.rightmost_screen_right,
                             self.rightmost_screen_top,
                             self.panel_width,
                             self.rightmost_screen_height)

        # Pin状态标志
        self.is_pinned = False
        
        # 拖拽调整宽度相关变量
        self.is_resizing = False
        self.resize_start_pos = None
        self.resize_start_width = 0
        self.resize_start_geometry = None
        self.is_edit_mode = False

        # 创建内容
        self.setup_ui()

        # 设置动画
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # 设置初始状态为隐藏
        self.is_visible = False
        self.is_animating = False

        # 创建全局事件过滤器
        self.mouse_detector = MouseDetector(self)
        QApplication.instance().installEventFilter(self.mouse_detector)

        # 创建检测鼠标位置的定时器
        self.detection_timer = QTimer(self)
        self.detection_timer.timeout.connect(self.check_mouse_position)
        self.detection_timer.start(300)

        # 创建屏幕配置变化检测定时器
        self.screen_update_timer = QTimer(self)
        self.screen_update_timer.timeout.connect(self.check_screen_changes)
        self.screen_update_timer.start(2000)  # 每2秒检查一次屏幕配置变化
        
        # 创建重绘定时器，解决亚克力效果的重绘问题
        if self.enable_aero:
            self.repaint_timer = QTimer(self)
            self.repaint_timer.timeout.connect(self.force_repaint)
            self.repaint_timer.start(1000)  # 每秒强制重绘一次

        # 启用鼠标跟踪，用于在编辑模式下实时检测鼠标位置
        self.setMouseTracking(True)

        # 添加延迟显示功能
        self.edge_hover_timer = QTimer(self)
        self.edge_hover_timer.setSingleShot(True)  # 单次触发
        self.edge_hover_timer.timeout.connect(self.delayed_show_panel)
        self.hover_delay = 500  # 悬停延迟时间（毫秒）
        self.last_edge_position = None  # 记录上次在边缘的鼠标位置

        self.windowEffect = WindowEffect()
        # 启用Aero效果
        if self.enable_aero:
            # 设置亚克力效果，添加适当的参数防止重绘问题
            # gradientColor: RGBA格式，设置半透明背景
            self.windowEffect.setAcrylicEffect(self.winId(), '99999960')
        else:
            self.windowEffect.setDefault(self.winId())

    def set_opacity(self, opacity):
        """设置背景透明度"""
        self.opacity = max(0.0, min(1.0, opacity))  # 确保在0-1范围内
        self.update()  # 重绘窗口

    def update_screen_info(self):
        """更新所有屏幕信息，找出最左侧和最右侧屏幕"""
        screens = QApplication.screens()

        # 找出最右侧的屏幕
        rightmost_screen = None
        rightmost_x = -float('inf')

        # 找出最左侧的屏幕
        leftmost_screen = None
        leftmost_x = float('inf')

        for screen in screens:
            geometry = screen.geometry()
            screen_right = geometry.x() + geometry.width()
            screen_left = geometry.x()

            if screen_right > rightmost_x:
                rightmost_x = screen_right
                rightmost_screen = screen

            if screen_left < leftmost_x:
                leftmost_x = screen_left
                leftmost_screen = screen

        # 保存最右侧屏幕的信息
        geometry = rightmost_screen.geometry()
        self.rightmost_screen_right = geometry.x() + geometry.width()
        self.rightmost_screen_top = geometry.y()
        self.rightmost_screen_height = geometry.height()
        self.rightmost_screen_left = geometry.x()

        # 保存最左侧屏幕的信息
        geometry = leftmost_screen.geometry()
        self.leftmost_screen_left = geometry.x()
        self.leftmost_screen_top = geometry.y()
        self.leftmost_screen_height = geometry.height()
        self.leftmost_screen_right = geometry.x() + geometry.width()

        # 保存所有屏幕的总体边界
        self.virtual_screen_width = 0
        self.virtual_screen_height = 0

        for screen in screens:
            geometry = screen.geometry()
            right_edge = geometry.x() + geometry.width()
            bottom_edge = geometry.y() + geometry.height()

            if right_edge > self.virtual_screen_width:
                self.virtual_screen_width = right_edge

            if bottom_edge > self.virtual_screen_height:
                self.virtual_screen_height = bottom_edge

    def check_screen_changes(self):
        """检查屏幕配置是否发生变化"""
        if self.position == self.LEFT:
            old_edge = self.leftmost_screen_left
            old_height = self.leftmost_screen_height
        else:  # RIGHT
            old_edge = self.rightmost_screen_right
            old_height = self.rightmost_screen_height

        self.update_screen_info()

        # 根据位置选择正确的屏幕信息
        if self.position == self.LEFT:
            new_edge = self.leftmost_screen_left
            new_height = self.leftmost_screen_height
            new_top = self.leftmost_screen_top
        else:  # RIGHT
            new_edge = self.rightmost_screen_right
            new_height = self.rightmost_screen_height
            new_top = self.rightmost_screen_top

        # 如果屏幕位置或尺寸变化，更新侧边栏位置
        if old_edge != new_edge or old_height != new_height:
            self.setFixedSize(self.panel_width, new_height)

            if self.is_visible:
                # 如果当前可见，更新到新的可见位置
                if self.position == self.LEFT:
                    self.setGeometry(new_edge, new_top,
                                     self.panel_width, new_height)
                else:  # RIGHT
                    self.setGeometry(new_edge - self.panel_width, new_top,
                                     self.panel_width, new_height)
            else:
                # 如果当前隐藏，更新到新的隐藏位置
                if self.position == self.LEFT:
                    self.setGeometry(new_edge - self.panel_width, new_top,
                                     self.panel_width, new_height)
                else:  # RIGHT
                    self.setGeometry(new_edge, new_top,
                                     self.panel_width, new_height)

    def paintEvent(self, event):
        """自定义绘制事件，实现磨砂效果背景"""
        if not self.enable_aero:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 计算颜色的alpha通道值（0-255）
            alpha_value = int(self.opacity * 255)

            # 创建渐变色背景
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(40, 40, 40, alpha_value))  # 顶部颜色
            gradient.setColorAt(1, QColor(30, 30, 30, alpha_value))  # 底部颜色

            painter.fillRect(self.rect(), QBrush(gradient))

            # 添加边框
            if self.position == self.LEFT:
                border_color = QColor(80, 80, 80, alpha_value)
                painter.setPen(border_color)
                painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
            else:  # RIGHT
                border_color = QColor(80, 80, 80, alpha_value)
                painter.setPen(border_color)
                painter.drawLine(0, 0, 0, self.height())
        else:
            # 亚克力模式下，确保背景被正确清除
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.rect(), Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        super().paintEvent(event)

    def setup_ui(self):
        # 创建主窗口部件
        central_widget = QWidget(self)
        # 只在非亚克力模式下设置透明背景
        if not self.enable_aero:
            central_widget.setAttribute(Qt.WA_TranslucentBackground)
        # 为中央部件也启用鼠标跟踪
        central_widget.setMouseTracking(True)
        self.setCentralWidget(central_widget)

        # 创建布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建顶部布局，包含标题和Pin按钮
        top_layout = QHBoxLayout()

        # 创建Pin按钮
        lock_icon = qtawesome.icon('fa.unlock', color='#DDD')
        self.pin_button = QPushButton(lock_icon, "")  # 使用emoji作为图标
        self.pin_button.setIconSize(QSize(24, 24))
        self.pin_button.setChecked(False)
        self.pin_button.setFixedSize(28, 28)
        self.pin_button.setCheckable(True)
        # 根据侧边栏位置设置按钮样式
        if self.position == self.LEFT:
            # 左侧侧边栏，按钮margin调整
            button_style = """
                QPushButton {
                    margin: 6px 0 0 6px;
                    font-size: 16px;
                    border: none;
                }
            """
        else:  # RIGHT
            # 右侧侧边栏，按钮margin调整
            button_style = """
                QPushButton {
                    margin: 6px 6px 0 0;
                    font-size: 16px;
                    border: none;
                }
            """
            
        self.pin_button.setStyleSheet(button_style)
        self.pin_button.clicked.connect(self.toggle_pin)

        edit_icon = qtawesome.icon('fa.edit', color='#DDD')
        self.edit_button = QPushButton(edit_icon, "")
        self.edit_button.setIconSize(QSize(24, 24))
        self.edit_button.setCheckable(True)
        self.edit_button.setChecked(False)
        self.edit_button.setStyleSheet(button_style)
        self.edit_button.clicked.connect(self.toggle_edit_mode)

        menu_icon = qtawesome.icon('fa.bars', color='#DDD')
        self.menu_button = MenuButton(menu_icon, '')
        self.menu_button.setIconSize(QSize(24, 24))
        self.menu_button.setStyleSheet(button_style)
        self._set_hide_button(self.menu_button, True)
        self.menu_button.set_menu(self._widget_menu)

        # 根据侧边栏位置设置按钮布局
        if self.position == self.LEFT:
            # 左侧侧边栏，按钮在左边，按顺序排列
            top_layout.addWidget(self.menu_button)
            top_layout.addWidget(self.edit_button)
            top_layout.addWidget(self.pin_button)
            top_layout.addStretch()  # 添加弹性空间推到右边
        else:  # RIGHT
            # 右侧侧边栏，按钮在右边
            top_layout.addStretch()  # 添加弹性空间推到左边
            top_layout.addWidget(self.menu_button)
            top_layout.addWidget(self.edit_button)
            top_layout.addWidget(self.pin_button)

        # 添加顶部布局到主布局
        main_layout.addLayout(top_layout)
        # 添加一些间距
        main_layout.addSpacing(0)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        self.content_view = ContentView()
        self.content_view.set_edit_mode(False)
        content_layout.addWidget(self.content_view)
        main_layout.addLayout(content_layout)

        self._register_sidebar_widget()

    def _register_sidebar_widget(self):
        widgets = discover_sidebar_widgets()
        widgets_by_category = {}
        for widget in widgets:
            category = getattr(widget, 'category', '未分类')
            if category not in widgets_by_category:
                widgets_by_category[category] = []
            widgets_by_category[category].append(widget)

        for category, widgets in widgets_by_category.items():
            category_menu = qfluentwidgets.RoundMenu(category, self._widget_menu)
            self._widget_menu.addMenu(category_menu)

            for widget in widgets:
                icon = getattr(widget, 'icon', None)
                if icon:
                    if not isinstance(icon, QIcon):
                        icon = qtawesome.icon(icon)

                action = qfluentwidgets.Action(
                        getattr(widget, 'name', '未命名'),
                        self,
                        triggered=lambda w=widget: self.content_view.add_widget(widget=w)
                    )
                action.setToolTip(getattr(widget, 'description', ''))
                category_menu.addAction(action)

        # 加载保存的节点配置
        self.content_view.load_nodes_from_config()

    def toggle_edit_mode(self):
        self.is_edit_mode = self.edit_button.isChecked()

        self.content_view.set_edit_mode(self.is_edit_mode)
        if self.is_edit_mode:
            self.edit_button.setIcon(qtawesome.icon('fa.check', color='#EEE'))
            self.edit_button.setToolTip("退出编辑模式")
            self._set_hide_button(self.menu_button, False)
            # 进入编辑模式时自动固定面板
            if not self.is_pinned:
                self.is_pinned = True
                self.pin_button.setChecked(True)
                self.pin_button.setIcon(qtawesome.icon('fa.lock', color='#EEE'))
                self.pin_button.setToolTip("取消固定面板")
        else:
            self.edit_button.setIcon(qtawesome.icon('fa.edit', color='#DDD'))
            self.edit_button.setToolTip("进入编辑模式")
            self._set_hide_button(self.menu_button, True)
            # 退出编辑模式时自动取消固定面板
            if self.is_pinned:
                self.is_pinned = False
                self.pin_button.setChecked(False)
                self.pin_button.setIcon(qtawesome.icon('fa.unlock', color='#DDD'))
                self.pin_button.setToolTip("固定面板")
            # 退出编辑模式时重置光标和拖拽状态
            self.setCursor(Qt.ArrowCursor)
            if self.is_resizing:
                self.is_resizing = False
                self.resize_start_pos = None
                self.resize_start_width = 0
                self.resize_start_geometry = None
                # 确保按钮在退出编辑模式时恢复透明度
                self._restore_button_opacity()

            qfluentwidgets.qconfig.set(config_model.super_sidebar_width, self.panel_width)

    def toggle_pin(self):
        """切换固定状态"""
        self.is_pinned = self.pin_button.isChecked()

        # 更新按钮提示
        if self.is_pinned:
            self.pin_button.setIcon(qtawesome.icon('fa.lock', color='#EEE'))
            self.pin_button.setToolTip("取消固定面板")
        else:
            self.pin_button.setIcon(qtawesome.icon('fa.unlock', color='#DDD'))
            self.pin_button.setToolTip("固定面板")
            # 取消固定时重置光标和拖拽状态
            self.setCursor(Qt.ArrowCursor)
            if self.is_resizing:
                self.is_resizing = False
                self.resize_start_pos = None
                self.resize_start_width = 0
                self.resize_start_geometry = None
                # 确保按钮在取消固定时恢复透明度
                self._restore_button_opacity()

    def _set_hide_button(self, button, hide):
        if hide:
            opacity_effect = QGraphicsOpacityEffect(self)
            opacity_effect.setOpacity(0.0)  # 完全透明
            button.setGraphicsEffect(opacity_effect)
        else:
            button.setGraphicsEffect(None)

    def _hide_buttons_with_opacity(self):
        """使用透明度效果隐藏按钮"""
        self._set_hide_button(self.edit_button, True)
        self._set_hide_button(self.pin_button, True)
        self._set_hide_button(self.menu_button, True)

    def _restore_button_opacity(self):
        """恢复按钮的正常透明度"""
        # 移除透明度效果，恢复按钮的正常显示
        self.edit_button.setGraphicsEffect(None)
        self.pin_button.setGraphicsEffect(None)
        self.menu_button.setGraphicsEffect(None)

    def check_mouse_position(self):
        if self.is_animating or self.is_pinned:  # 如果已固定，不检查鼠标位置
            return

        mouse_pos = QCursor.pos()
        activation_zone = 5  # 距离屏幕边缘的激活区域像素数

        if self.position == self.LEFT:
            # 检查鼠标是否在最左侧屏幕上
            is_on_target_screen = (
                mouse_pos.x() >= self.leftmost_screen_left and
                mouse_pos.x() <= self.leftmost_screen_right and
                mouse_pos.y() >= self.leftmost_screen_top and
                mouse_pos.y() <= self.leftmost_screen_top + self.leftmost_screen_height
            )

            # 判断鼠标是否在最左侧屏幕的左侧边缘
            is_at_edge = mouse_pos.x() - self.leftmost_screen_left <= activation_zone

            if is_on_target_screen and is_at_edge and not self.is_visible:
                # 检查鼠标是否已经在边缘停留
                if self.edge_hover_timer.isActive():
                    # 如果鼠标移动了太多，重置计时器
                    if self.last_edge_position and (
                            abs(mouse_pos.y() - self.last_edge_position.y()) > 5):
                        self.last_edge_position = QPoint(mouse_pos)
                        self.edge_hover_timer.start(self.hover_delay)
                else:
                    # 开始计时
                    self.last_edge_position = QPoint(mouse_pos)
                    self.edge_hover_timer.start(self.hover_delay)
            elif not is_at_edge and self.edge_hover_timer.isActive():
                # 如果鼠标离开了边缘，停止计时器
                self.edge_hover_timer.stop()

            if (not self.geometry().contains(mouse_pos) and
                    self.is_visible and
                    mouse_pos.x() > self.leftmost_screen_left + self.panel_width):
                self.hide_panel()
        else:  # RIGHT
            # 检查鼠标是否在最右侧屏幕上
            is_on_target_screen = (
                mouse_pos.x() >= self.rightmost_screen_left and
                mouse_pos.x() <= self.rightmost_screen_right and
                mouse_pos.y() >= self.rightmost_screen_top and
                mouse_pos.y() <= self.rightmost_screen_top + self.rightmost_screen_height
            )

            # 判断鼠标是否在最右侧屏幕的右侧边缘
            is_at_edge = self.rightmost_screen_right - mouse_pos.x() <= activation_zone

            if is_on_target_screen and is_at_edge and not self.is_visible:
                # 检查鼠标是否已经在边缘停留
                if self.edge_hover_timer.isActive():
                    # 如果鼠标移动了太多，重置计时器
                    if self.last_edge_position and (
                            abs(mouse_pos.y() - self.last_edge_position.y()) > 5):
                        self.last_edge_position = QPoint(mouse_pos)
                        self.edge_hover_timer.start(self.hover_delay)
                else:
                    # 开始计时
                    self.last_edge_position = QPoint(mouse_pos)
                    self.edge_hover_timer.start(self.hover_delay)
            elif not is_at_edge and self.edge_hover_timer.isActive():
                # 如果鼠标离开了边缘，停止计时器
                self.edge_hover_timer.stop()

            if (not self.geometry().contains(mouse_pos) and
                    self.is_visible and
                    mouse_pos.x() < self.rightmost_screen_right - self.panel_width):
                self.hide_panel()

    def delayed_show_panel(self):
        """在延迟后显示面板"""
        # 再次检查鼠标位置，确保鼠标仍在边缘
        mouse_pos = QCursor.pos()
        activation_zone = 5

        if self.position == self.LEFT:
            is_on_target_screen = (
                mouse_pos.x() >= self.leftmost_screen_left and
                mouse_pos.x() <= self.leftmost_screen_right and
                mouse_pos.y() >= self.leftmost_screen_top and
                mouse_pos.y() <= self.leftmost_screen_top + self.leftmost_screen_height
            )
            is_at_edge = mouse_pos.x() - self.leftmost_screen_left <= activation_zone
        else:  # RIGHT
            is_on_target_screen = (
                mouse_pos.x() >= self.rightmost_screen_left and
                mouse_pos.x() <= self.rightmost_screen_right and
                mouse_pos.y() >= self.rightmost_screen_top and
                mouse_pos.y() <= self.rightmost_screen_top + self.rightmost_screen_height
            )
            is_at_edge = self.rightmost_screen_right - mouse_pos.x() <= activation_zone

        if is_on_target_screen and is_at_edge:
            self.show_panel()

    def show_panel(self):
        if self.is_visible or self.is_animating:
            return

        self.is_animating = True

        # 先确保窗口在正确的初始位置，但还不显示
        if self.position == self.LEFT:
            self.setGeometry(self.leftmost_screen_left - self.panel_width,
                             self.leftmost_screen_top,
                             self.panel_width,
                             self.leftmost_screen_height)

            start_rect = QRect(self.leftmost_screen_left - self.panel_width,
                               self.leftmost_screen_top,
                               self.panel_width,
                               self.leftmost_screen_height)
            end_rect = QRect(self.leftmost_screen_left,
                             self.leftmost_screen_top,
                             self.panel_width,
                             self.leftmost_screen_height)
        else:  # RIGHT
            self.setGeometry(self.rightmost_screen_right,
                             self.rightmost_screen_top,
                             self.panel_width,
                             self.rightmost_screen_height)

            start_rect = QRect(self.rightmost_screen_right,
                               self.rightmost_screen_top,
                               self.panel_width,
                               self.rightmost_screen_height)
            end_rect = QRect(self.rightmost_screen_right - self.panel_width,
                             self.rightmost_screen_top,
                             self.panel_width,
                             self.rightmost_screen_height)

        # 先显示窗口，然后立即开始动画
        self.show()

        # 设置动画
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)

        # 断开之前可能的连接以避免多次触发
        try:
            self.animation.finished.disconnect()
        except RuntimeError:
            pass  # 如果没有连接，忽略错误

        self.animation.finished.connect(self.on_show_finished)

        # 立即开始动画
        QTimer.singleShot(0, self.animation.start)

    def hide_panel(self):
        if not self.is_visible or self.is_animating or self.is_pinned:  # 如果已固定，不隐藏
            return

        self.is_animating = True

        if self.position == self.LEFT:
            start_rect = QRect(self.leftmost_screen_left,
                               self.leftmost_screen_top,
                               self.panel_width,
                               self.leftmost_screen_height)
            end_rect = QRect(self.leftmost_screen_left - self.panel_width,
                             self.leftmost_screen_top,
                             self.panel_width,
                             self.leftmost_screen_height)
        else:  # RIGHT
            start_rect = QRect(self.rightmost_screen_right - self.panel_width,
                               self.rightmost_screen_top,
                               self.panel_width,
                               self.rightmost_screen_height)
            end_rect = QRect(self.rightmost_screen_right,
                             self.rightmost_screen_top,
                             self.panel_width,
                             self.rightmost_screen_height)

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)

        # 断开之前可能的连接以避免多次触发
        try:
            self.animation.finished.disconnect()
        except RuntimeError:
            pass  # 如果没有连接，忽略错误

        self.animation.finished.connect(self.on_hide_finished)
        self.animation.start()

    def on_show_finished(self):
        self.is_animating = False
        self.is_visible = True

    def on_hide_finished(self):
        self.is_animating = False
        self.is_visible = False
        self.hide()  # 动画完成后隐藏窗口

    def force_repaint(self):
        """强制重绘窗口，解决亚克力效果的重绘问题"""
        if self.is_visible and self.enable_aero:
            self.update()
            # 强制重绘所有子组件
            for child in self.findChildren(QWidget):
                child.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_edit_mode and self.is_pinned:
            if self.is_in_resize_area(event.pos()):
                self.is_resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_width = self.panel_width
                self.resize_start_geometry = self.geometry()
                self.setCursor(Qt.SizeHorCursor)
                # 使用透明度效果隐藏按钮，但保持布局
                self._hide_buttons_with_opacity()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_edit_mode and self.is_pinned:
            if self.is_resizing:
                # 正在拖拽调整宽度
                self.handle_resize_drag(event.globalPos())
                event.accept()
                return
            else:
                # 检查是否在可调整大小的区域内
                if self.is_in_resize_area(event.pos()):
                    self.setCursor(Qt.SizeHorCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
        else:
            # 非编辑模式或未固定时使用默认光标
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_resizing:
            self.is_resizing = False
            self.resize_start_pos = None
            self.resize_start_width = 0
            self.resize_start_geometry = None
            self.setCursor(Qt.ArrowCursor)
            # 拖动完成后恢复按钮透明度
            self._restore_button_opacity()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def is_in_resize_area(self, pos):
        """检查鼠标位置是否在可调整大小的区域内"""
        if not self.is_edit_mode or not self.is_pinned:
            return False
            
        if self.position == self.RIGHT:
            # 右侧侧边栏，左边缘可调整
            return pos.x() <= self.RESIZE_BORDER_WIDTH
        else:  # LEFT
            # 左侧侧边栏，右边缘可调整
            return pos.x() >= self.width() - self.RESIZE_BORDER_WIDTH

    def handle_resize_drag(self, global_pos):
        """处理拖拽调整宽度"""
        if not self.resize_start_pos or not self.resize_start_geometry:
            return
            
        # 计算鼠标移动的距离
        delta_x = global_pos.x() - self.resize_start_pos.x()
        
        # 根据侧边栏位置调整宽度计算方式
        if self.position == self.RIGHT:
            # 右侧侧边栏，向左拖拽增加宽度，向右拖拽减少宽度
            new_width = self.resize_start_width - delta_x
        else:  # LEFT
            # 左侧侧边栏，向右拖拽增加宽度，向左拖拽减少宽度
            new_width = self.resize_start_width + delta_x
            
        # 限制宽度范围
        new_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, new_width))
        
        # 更新窗口尺寸和位置
        self.update_size_and_position(new_width)

    def update_size_and_position(self, new_width):
        """更新窗口大小和位置"""
        self.panel_width = new_width
        
        if self.position == self.RIGHT:
            # 右侧侧边栏需要调整x坐标以保持右边缘位置不变
            if self.is_visible:
                new_x = self.rightmost_screen_right - new_width
                new_y = self.rightmost_screen_top
                new_height = self.rightmost_screen_height
            else:
                new_x = self.rightmost_screen_right
                new_y = self.rightmost_screen_top  
                new_height = self.rightmost_screen_height
        else:  # LEFT
            # 左侧侧边栏保持左边缘位置不变
            if self.is_visible:
                new_x = self.leftmost_screen_left
                new_y = self.leftmost_screen_top
                new_height = self.leftmost_screen_height
            else:
                new_x = self.leftmost_screen_left - new_width
                new_y = self.leftmost_screen_top
                new_height = self.leftmost_screen_height
                
        # 设置新的几何尺寸
        self.setGeometry(new_x, new_y, new_width, new_height)
        self.setFixedSize(new_width, new_height)
        self.repaint()


class MouseDetector(QObject):
    def __init__(self, panel):
        super().__init__()
        self.panel = panel

    def eventFilter(self, obj, event):
        # 仅作为备份检测机制
        return super().eventFilter(obj, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建侧边栏，可以指定位置为 SiderBar.LEFT 或 SiderBar.RIGHT
    # 第二个参数是透明度，范围0.0-1.0
    panel = SuperSidebar(SuperSidebar.RIGHT, opacity=0.9)  # 右侧显示，透明度0.6

    # 您也可以在任何时候动态修改透明度
    # panel.set_opacity(0.3)  # 更改为更透明的背景

    sys.exit(app.exec_())
