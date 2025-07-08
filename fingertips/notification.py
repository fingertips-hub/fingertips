import sys
from PySide2 import QtWidgets, QtCore, QtGui
import qtawesome as qta


class NotificationWidget(QtWidgets.QWidget):
    """
    灵动岛风格通知组件
    支持从屏幕顶部滑入、点击展开/折叠、定时关闭等功能
    """
    
    # 信号定义
    notification_clicked = QtCore.Signal()
    notification_closed = QtCore.Signal()
    closing_started = QtCore.Signal()  # 开始关闭信号
    size_changed = QtCore.Signal()  # 尺寸变化完成信号
    
    def __init__(self, title="通知", message="", icon_name="fa.info-circle", 
                 auto_close_time=5000, parent=None):
        super().__init__(parent)
        
        # 基本属性
        self.title = title
        self.message = message
        self.icon_name = icon_name
        self.auto_close_time = auto_close_time
        
        # 状态管理
        self.is_expanded = False
        self.is_visible = False
        self.is_animating = False
        self.is_closing = False  # 是否正在关闭
        self.is_expanding_or_collapsing = False  # 是否正在展开/折叠
        
        # 尺寸定义
        self.collapsed_width = 300
        self.collapsed_height = 60
        self.expanded_width = 400
        self.expanded_height = 120
        
        # 动画组件
        self.slide_animation = None
        self.expand_animation = None
        self.position_animation = None  # 位置调整动画
        self.opacity_animation = None
        
        # 定时器
        self.auto_close_timer = QtCore.QTimer()
        self.auto_close_timer.timeout.connect(self.close_notification)
        
        # 初始化UI
        self._init_ui()
        self._init_animations()
        self._setup_position()
        
    def _init_ui(self):
        """初始化用户界面"""
        # 窗口属性设置
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | 
            QtCore.Qt.WindowStaysOnTopHint | 
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, False)
        
        # 不使用setFixedSize，让窗口可以动画化尺寸
        self.resize(self.collapsed_width, self.collapsed_height)
        
        # 主容器
        self.main_container = QtWidgets.QWidget()
        self.main_container.setObjectName("notification_container")
        
        # 布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_container)
        
        # 使用水平布局作为主布局（折叠状态）
        self.main_layout = QtWidgets.QHBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(12)
        
        # 图标
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon = qta.icon(self.icon_name, color='#2196F3')
        pixmap = icon.pixmap(24, 24)
        self.icon_label.setPixmap(pixmap)
        
        # 中央内容容器
        self.content_container = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        
        # 标题（居中）
        self.title_label = QtWidgets.QLabel(self.title)
        self.title_label.setObjectName("notification_title")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # 消息内容（居中）
        self.message_label = QtWidgets.QLabel(self.message)
        self.message_label.setObjectName("notification_message")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(QtCore.Qt.AlignCenter)
        self.message_label.setVisible(False)  # 初始隐藏
        
        # 添加到内容容器
        self.content_layout.addStretch()  # 上方弹性空间
        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.message_label)
        self.content_layout.addStretch()  # 下方弹性空间
        
        # 关闭按钮
        self.close_button = QtWidgets.QPushButton()
        self.close_button.setFixedSize(20, 20)
        self.close_button.setObjectName("notification_close_button")
        close_icon = qta.icon('fa.times', color='#666666')
        self.close_button.setIcon(close_icon)
        self.close_button.setIconSize(QtCore.QSize(12, 12))
        self.close_button.clicked.connect(self.close_notification)
        
        # 添加到主布局
        self.main_layout.addWidget(self.icon_label)
        self.main_layout.addWidget(self.content_container, 1)
        self.main_layout.addWidget(self.close_button)
        
        # 应用样式
        self._apply_styles()
        
        # 确保初始状态正确显示
        self.update()
        
    def _apply_styles(self):
        """应用灵动岛风格样式"""
        style = """
        QWidget#notification_container {
            background-color: transparent;
            border: none;
        }
        
        QLabel#notification_title {
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            margin: 0px;
            padding: 0px;
        }
        
        QLabel#notification_message {
            color: #cccccc;
            font-size: 12px;
            margin: 0px;
            padding: 4px 0px;
            line-height: 1.4;
        }
        
        QPushButton#notification_close_button {
            background-color: transparent;
            border: none;
            border-radius: 10px;
            padding: 0px;
        }
        
        QPushButton#notification_close_button:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        QPushButton#notification_close_button:pressed {
            background-color: rgba(255, 255, 255, 0.2);
        }
        """
        self.setStyleSheet(style)
        
    def paintEvent(self, event):
        """自定义绘制事件，确保圆角背景"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        
        # 清空背景
        painter.fillRect(self.rect(), QtCore.Qt.transparent)
        
        # 绘制圆角背景
        rect = self.rect().adjusted(1, 1, -1, -1)  # 轻微缩小避免边缘锯齿
        painter.setBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30, 230)))  # 半透明黑色
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 25), 1))  # 半透明白边
        painter.drawRoundedRect(rect, 30, 30)
        
        # 不调用父类的paintEvent，因为我们已经绘制了背景
        
    def resizeEvent(self, event):
        """窗口尺寸变化事件"""
        super().resizeEvent(event)
        # 强制重绘以保持圆角效果
        self.update()
        
    def _init_animations(self):
        """初始化动画系统"""
        # 滑动动画（用于显示/隐藏）
        self.slide_animation = QtCore.QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(600)
        self.slide_animation.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        self.slide_animation.valueChanged.connect(self.update)  # 动画时更新绘制
        
        # 展开/折叠动画（用于尺寸和位置变化）
        self.expand_animation = QtCore.QPropertyAnimation(self, b"geometry")
        self.expand_animation.setDuration(400)
        self.expand_animation.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        self.expand_animation.valueChanged.connect(self.update)  # 动画时更新绘制
        
        # 位置调整动画（用于多通知位置调整）
        self.position_animation = QtCore.QPropertyAnimation(self, b"pos")
        self.position_animation.setDuration(400)  # 统一为400ms
        self.position_animation.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        
    def _setup_position(self):
        """设置通知位置"""
        desktop = QtWidgets.QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        
        # 计算初始位置（屏幕顶部中央，向上隐藏）
        x = (screen_geometry.width() - self.collapsed_width) // 2
        y = -self.collapsed_height
        
        self.setGeometry(x, y, self.collapsed_width, self.collapsed_height)
        
    def show_notification(self):
        """显示通知（滑入动画）"""
        if self.is_visible or self.is_animating:
            return
            
        self.is_animating = True
        self.is_visible = True
        
        # 显示窗口
        self.show()
        self.update()  # 确保圆角正确显示
        
        # 计算目标位置
        desktop = QtWidgets.QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        x = (screen_geometry.width() - self.collapsed_width) // 2
        y = 20  # 距离顶部的间距
        
        # 清理之前的连接
        try:
            self.slide_animation.finished.disconnect()
        except:
            pass
            
        # 滑入动画
        self.slide_animation.setStartValue(self.geometry())
        self.slide_animation.setEndValue(QtCore.QRect(x, y, self.collapsed_width, self.collapsed_height))
        self.slide_animation.finished.connect(self._on_slide_in_finished)
        self.slide_animation.start()
        
    def _on_slide_in_finished(self):
        """滑入动画完成"""
        self.is_animating = False
        try:
            self.slide_animation.finished.disconnect()
        except:
            pass
        
        # 确保圆角正确显示
        self.update()
        
        # 启动自动关闭定时器
        if self.auto_close_time > 0:
            self.auto_close_timer.start(self.auto_close_time)
            
    def close_notification(self):
        """关闭通知（滑出动画）"""
        if not self.is_visible or self.is_animating:
            return
            
        self.is_animating = True
        self.is_closing = True
        
        # 停止自动关闭定时器
        self.auto_close_timer.stop()
        
        # 直接开始滑出动画，保持当前显示状态
        self.closing_started.emit()
        self._start_slide_out()
            
    def _start_slide_out(self):
        """开始滑出动画"""
        # 计算目标位置（向上滑出）
        current_rect = self.geometry()
        target_rect = QtCore.QRect(current_rect.x(), -self.height(), 
                                  current_rect.width(), current_rect.height())
        
        # 清理之前的连接
        try:
            self.slide_animation.finished.disconnect()
        except:
            pass
            
        # 滑出动画
        self.slide_animation.setStartValue(current_rect)
        self.slide_animation.setEndValue(target_rect)
        self.slide_animation.finished.connect(self._on_slide_out_finished)
        self.slide_animation.start()
        
    def _on_slide_out_finished(self):
        """滑出动画完成"""
        self.is_animating = False
        self.is_visible = False
        try:
            self.slide_animation.finished.disconnect()
        except:
            pass
        
        # 隐藏窗口
        self.hide()
        
        # 发送关闭信号
        self.notification_closed.emit()
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == QtCore.Qt.LeftButton:
            # 使用简单的区域检测，右侧30像素为关闭按钮区域
            if event.pos().x() < self.width() - 30:
                if not self.is_animating:
                    self.toggle_expansion()
                self.notification_clicked.emit()
        super().mousePressEvent(event)
        
    def toggle_expansion(self):
        """切换展开/折叠状态"""
        if self.is_expanded:
            self._collapse_notification()
        else:
            self._expand_notification()
            
    def _expand_notification(self):
        """展开通知"""
        if self.is_expanded or self.is_animating:
            return
            
        # 停止任何进行中的动画
        if self.expand_animation.state() == QtCore.QAbstractAnimation.Running:
            self.expand_animation.stop()
            
        self.is_animating = True
        self.is_expanded = True
        self.is_expanding_or_collapsing = True
        
        # 展开时让标题逐渐隐藏，避免抖动
        self._animate_title_fade_out()
        
        # 计算新位置和尺寸
        desktop = QtWidgets.QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        x = (screen_geometry.width() - self.expanded_width) // 2
        y = self.y()  # 保持当前Y位置
        
        # 使用几何动画同时动画化位置和尺寸
        current_rect = self.geometry()
        target_rect = QtCore.QRect(x, y, self.expanded_width, self.expanded_height)
        
        # 清理之前的连接
        try:
            self.expand_animation.finished.disconnect()
        except:
            pass
            
        self.expand_animation.setStartValue(current_rect)
        self.expand_animation.setEndValue(target_rect)
        self.expand_animation.finished.connect(self._on_expand_finished)
        self.expand_animation.start()
        
        # 延迟显示详细信息，让动画先进行一部分，避免文字抖动
        QtCore.QTimer.singleShot(150, lambda: self.message_label.setVisible(True))
        
        # 延迟发送尺寸变化信号，让当前通知的动画先开始
        QtCore.QTimer.singleShot(50, self.size_changed.emit)
        
    def _on_expand_finished(self):
        """展开动画完成"""
        self.is_animating = False
        self.is_expanding_or_collapsing = False
        try:
            self.expand_animation.finished.disconnect()
        except:
            pass
        
        # 确保圆角正确显示
        self.update()
        
        # 展开完成后，再次调整位置确保所有通知位置正确
        self.size_changed.emit()
        
    def _collapse_notification(self):
        """折叠通知"""
        if not self.is_expanded or self.is_animating:
            return
            
        # 停止任何进行中的动画
        if self.expand_animation.state() == QtCore.QAbstractAnimation.Running:
            self.expand_animation.stop()
            
        self.is_animating = True
        self.is_expanded = False
        self.is_expanding_or_collapsing = True
        
        # 立即隐藏详细信息，避免动画过程中的布局重新计算导致抖动
        self.message_label.setVisible(False)
        
        # 收起时让标题逐渐显示，避免抖动
        self._animate_title_fade_in()
        
        # 计算新位置和尺寸
        desktop = QtWidgets.QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        x = (screen_geometry.width() - self.collapsed_width) // 2
        y = self.y()  # 保持当前Y位置
        
        # 使用几何动画同时动画化位置和尺寸
        current_rect = self.geometry()
        target_rect = QtCore.QRect(x, y, self.collapsed_width, self.collapsed_height)
        
        # 清理之前的连接
        try:
            self.expand_animation.finished.disconnect()
        except:
            pass
            
        self.expand_animation.setStartValue(current_rect)
        self.expand_animation.setEndValue(target_rect)
        self.expand_animation.finished.connect(self._on_collapse_finished)
        
        self.expand_animation.start()
        
        # 延迟发送尺寸变化信号，让当前通知的动画先开始
        QtCore.QTimer.singleShot(50, self.size_changed.emit)
        
    def _on_collapse_finished(self):
        """折叠动画完成"""
        self.is_animating = False
        self.is_expanding_or_collapsing = False
        try:
            self.expand_animation.finished.disconnect()
        except:
            pass
        
        # 确保圆角正确显示
        self.update()
        
        # 折叠完成后，再次调整位置确保所有通知位置正确
        self.size_changed.emit()
        
    def animate_to_position(self, target_pos):
        """动画移动到目标位置"""
        # 如果目标位置与当前位置相同（允许小误差），不进行动画
        if abs(self.pos().x() - target_pos.x()) < 2 and abs(self.pos().y() - target_pos.y()) < 2:
            return
            
        # 停止当前的位置动画
        if self.position_animation.state() == QtCore.QAbstractAnimation.Running:
            self.position_animation.stop()
            
        # 设置动画参数
        self.position_animation.setStartValue(self.pos())
        self.position_animation.setEndValue(target_pos)
        self.position_animation.start()
        
    def get_current_height(self):
        """获取当前通知的实际高度"""
        if self.is_expanded:
            return self.expanded_height
        else:
            return self.collapsed_height
            
    def can_adjust_position(self):
        """检查是否可以进行位置调整"""
        return (self.is_visible and 
                not self.is_closing and 
                not self.is_expanding_or_collapsing and
                not self.is_animating)
    
    def _animate_title_fade_out(self):
        """展开时让标题逐渐隐藏并从布局中移除"""
        # 创建透明度效果
        self.title_opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self.title_label.setGraphicsEffect(self.title_opacity_effect)
        
        # 创建透明度动画
        self.title_fade_animation = QtCore.QPropertyAnimation(self.title_opacity_effect, b"opacity")
        self.title_fade_animation.setDuration(200)  # 稍微缩短动画时间
        self.title_fade_animation.setStartValue(1.0)
        self.title_fade_animation.setEndValue(0.0)
        self.title_fade_animation.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        
        # 动画完成后从布局中移除标题，让message_label真正居中
        self.title_fade_animation.finished.connect(self._remove_title_from_layout)
        self.title_fade_animation.start()
        
    def _remove_title_from_layout(self):
        """从布局中移除标题，让message_label真正居中"""
        # 从布局中移除标题
        self.content_layout.removeWidget(self.title_label)
        self.title_label.setParent(None)
        
        # 清理透明度效果
        self.title_label.setGraphicsEffect(None)
        
    def _animate_title_fade_in(self):
        """收起时让标题逐渐显示并重新加入布局"""
        # 先将标题重新加入布局
        self._add_title_to_layout()
        
        # 创建透明度效果
        self.title_opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self.title_label.setGraphicsEffect(self.title_opacity_effect)
        
        # 创建透明度动画
        self.title_fade_animation = QtCore.QPropertyAnimation(self.title_opacity_effect, b"opacity")
        self.title_fade_animation.setDuration(200)  # 稍微缩短动画时间
        self.title_fade_animation.setStartValue(0.0)
        self.title_fade_animation.setEndValue(1.0)
        self.title_fade_animation.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        
        # 动画完成后移除graphics effect，恢复正常状态
        self.title_fade_animation.finished.connect(self._remove_title_effect)
        self.title_fade_animation.start()
        
    def _add_title_to_layout(self):
        """将标题重新加入布局"""
        # 检查标题是否已经在布局中
        if self.title_label.parent() == self.content_container:
            return
            
        # 重新设置父级
        self.title_label.setParent(self.content_container)
        
        # 重新加入布局（在stretch和message_label之间）
        self.content_layout.insertWidget(1, self.title_label)
        
    def _remove_title_effect(self):
        """移除标题的透明度效果，恢复正常状态"""
        self.title_label.setGraphicsEffect(None)

 
class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notifications = []
        self.max_notifications = 5
        self.notification_spacing = 10
        
    def show_notification(self, title, message="", icon_name="fa.info-circle", 
                         auto_close_time=5000):
        """显示通知"""
        # 移除过多的通知
        while len(self.notifications) >= self.max_notifications:
            old_notification = self.notifications.pop(0)
            old_notification.close_notification()
            
        # 创建新通知
        notification = NotificationWidget(
            title=title,
            message=message,
            icon_name=icon_name,
            auto_close_time=auto_close_time
        )
        
        # 连接信号
        notification.notification_closed.connect(
            lambda: self._remove_notification(notification)
        )
        # 连接尺寸变化信号以触发位置调整
        notification.size_changed.connect(self._adjust_notifications_position)
        # 连接开始关闭信号以触发位置调整
        notification.closing_started.connect(self._adjust_notifications_position)
        
        # 添加到列表
        self.notifications.append(notification)
        
        # 计算新通知的目标位置
        desktop = QtWidgets.QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        
        # 计算应该显示的Y位置（所有现有通知的累积高度）
        target_y = 20
        for existing_notification in self.notifications[:-1]:  # 不包括刚添加的
            if existing_notification.is_visible:
                target_y += existing_notification.get_current_height() + self.notification_spacing
        
        # 设置新通知的初始位置
        x = (screen_geometry.width() - notification.collapsed_width) // 2
        notification.setGeometry(x, -notification.collapsed_height, 
                               notification.collapsed_width, notification.collapsed_height)
        
        # 显示通知，滑入到正确位置
        notification.show()
        notification.update()
        
        # 滑入到目标位置
        notification.is_animating = True
        notification.is_visible = True
        
        # 清理之前的连接
        try:
            notification.slide_animation.finished.disconnect()
        except:
            pass
            
        notification.slide_animation.setStartValue(notification.geometry())
        notification.slide_animation.setEndValue(QtCore.QRect(x, target_y, 
                                                             notification.collapsed_width, 
                                                             notification.collapsed_height))
        notification.slide_animation.finished.connect(notification._on_slide_in_finished)
        notification.slide_animation.start()
        
        return notification
        
    def _remove_notification(self, notification):
        """移除通知"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.deleteLater()
            
        # 延迟重新调整位置，确保删除完成
        QtCore.QTimer.singleShot(50, self._adjust_notifications_position)
        
    def _adjust_notifications_position(self):
        """调整通知位置"""
        desktop = QtWidgets.QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        
        current_y = 20  # 起始Y位置
        
        for i, notification in enumerate(self.notifications):
            if notification.is_visible and not notification.is_closing:
                # 根据通知的当前状态计算x位置
                if notification.is_expanded:
                    x = (screen_geometry.width() - notification.expanded_width) // 2
                else:
                    x = (screen_geometry.width() - notification.collapsed_width) // 2
                
                # 计算目标位置
                target_pos = QtCore.QPoint(x, current_y)
                
                # 只有可以调整位置的通知才进行位置调整
                if notification.can_adjust_position():
                    # 使用动画移动到目标位置
                    notification.animate_to_position(target_pos)
                
                # 更新下一个通知的Y位置（当前通知高度 + 间距）
                current_y += notification.get_current_height() + self.notification_spacing
                
    def close_all_notifications(self):
        """关闭所有通知"""
        for notification in self.notifications[:]:
            notification.close_notification()


# 全局通知管理器实例
notification_manager = NotificationManager()


def show_notification(title, message="", icon_name="fa.info-circle", auto_close_time=5000):
    """便捷函数：显示通知"""
    return notification_manager.show_notification(title, message, icon_name, auto_close_time)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    
    # 测试抖动修复效果
    print("测试多通知展开/折叠动画，检查是否有抖动...")
    
    show_notification(
        title="第一个通知 - 点击测试展开",
        message="这是第一个通知的详细信息。点击可以展开查看更多内容。测试展开时其他通知的位置调整是否流畅。",
        icon_name="fa.info-circle",
        auto_close_time=0  # 不自动关闭，方便测试
    )

    show_notification(
        title="第二个通知 - 观察位置变化",
        message="这是第二个通知的详细信息。观察当第一个通知展开时，这个通知是否平滑下移。",
        icon_name="fa.warning",
        auto_close_time=0
    )

    show_notification(
        title="第三个通知 - 检查动画同步",
        message="这是第三个通知的详细信息。检查所有通知的动画是否同步，无抖动。",
        icon_name="fa.check-circle",
        auto_close_time=0
    )
    
    print("提示：")
    print("1. 点击第一个通知展开，观察其他通知是否平滑下移")
    print("2. 再次点击第一个通知折叠，观察其他通知是否平滑上移")
    print("3. 点击关闭按钮，观察其他通知是否平滑上移填补空间")

    app.exec_()