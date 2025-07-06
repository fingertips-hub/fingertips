"""
多平台热搜侧边栏组件
支持知乎、抖音、Bilibili、今日头条、微博五个平台的热搜数据展示
"""

import sys
import webbrowser
from typing import Dict, List
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton,  QSizePolicy,
    QScrollArea, QStackedWidget
)
from PySide2.QtCore import Qt, QTimer, QThread, Signal, QUrl
from PySide2.QtGui import QCursor, QPainter, QPen, QBrush, QColor, QDesktopServices
from PySide2.QtWidgets import QApplication
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget

# 导入API模块
from fingertips.sidebar_widgets.hotspot_card.douyin_api import DouyinHotspotAPI
from fingertips.sidebar_widgets.hotspot_card.bilibili_api import BilibiliHotspotAPI
from fingertips.sidebar_widgets.hotspot_card.toutiao_api import ToutiaoHotspotAPI
from fingertips.sidebar_widgets.hotspot_card.weibo_api import WeiboHotspotAPI


class HotspotDataThread(QThread):
    """热搜数据获取线程"""
    data_fetched = Signal(str, list)  # 平台名称, 数据列表
    error_occurred = Signal(str, str)  # 平台名称, 错误信息
    
    def __init__(self, platform: str, api_instance, limit: int = 15):
        super().__init__()
        self.platform = platform
        self.api_instance = api_instance
        self.limit = limit
        
    def run(self):
        try:
            hotspots = self.api_instance.fetch_hotspots(self.limit)
            self.data_fetched.emit(self.platform, hotspots)
        except Exception as e:
            self.error_occurred.emit(self.platform, str(e))


class HotspotItemWidget(QWidget):
    """单个热搜项组件"""
    
    def __init__(self, hotspot_data: Dict, parent=None):
        super().__init__(parent)
        self.hotspot_data = hotspot_data
        self.is_clicked = False
        self.double_click_timer = QTimer()
        self.double_click_timer.setSingleShot(True)
        self.double_click_timer.timeout.connect(self.handle_single_click)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        self.setFixedHeight(60)
        
        # 设置样式 - 只设置基本样式
        self.setStyleSheet("border: none; background: transparent;")
        
        # 设置自动填充背景
        self.setAutoFillBackground(False)
        
        # 设置鼠标悬停样式
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMouseTracking(True)

        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # 排名标签
        rank_label = QLabel(str(self.hotspot_data.get('rank', 0)))
        rank_label.setFixedSize(24, 24)
        rank_label.setAlignment(Qt.AlignCenter)
        rank_label.setStyleSheet("""
            QLabel {
                background-color: #007bff;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # 前3名特殊颜色
        rank = self.hotspot_data.get('rank', 0)
        if rank == 1:
            rank_label.setStyleSheet(rank_label.styleSheet().replace('#007bff', '#ff6b6b'))
        elif rank == 2:
            rank_label.setStyleSheet(rank_label.styleSheet().replace('#007bff', '#ffa500'))
        elif rank == 3:
            rank_label.setStyleSheet(rank_label.styleSheet().replace('#007bff', '#4ecdc4'))
        
        layout.addWidget(rank_label)
        
        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # 标题
        title_label = QLabel(self.hotspot_data.get('title', ''))
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
        """)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(32)
        content_layout.addWidget(title_label)
        
        # 热度信息
        heat_label = QLabel(self.hotspot_data.get('heat', ''))
        heat_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        content_layout.addWidget(heat_label)
        
        layout.addLayout(content_layout, 1)

    def mousePressEvent(self, event):
        """鼠标点击事件 - 延迟处理单击"""
        if event.button() == Qt.LeftButton:
            # 启动定时器，延迟处理单击事件
            self.double_click_timer.start(300)  # 300ms延迟
            
        super().mousePressEvent(event)
    
    def handle_single_click(self):
        """处理单击事件 - 复制标题到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.hotspot_data.get('title', ''))
        
        # 简单的视觉反馈
        self.is_clicked = True
        self.update()
        
        # 恢复样式
        QTimer.singleShot(200, self.reset_click_state)
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 打开链接"""
        if event.button() == Qt.LeftButton:
            # 取消单击事件的定时器
            self.double_click_timer.stop()
            
            # 获取链接URL
            url = self.hotspot_data.get('url', '')
            if url:
                try:
                    # 使用Qt的方式打开链接
                    QDesktopServices.openUrl(QUrl(url))
                    print(f"已打开链接: {url}")
                except Exception as e:
                    # 备用方式：使用webbrowser模块
                    try:
                        webbrowser.open(url)
                        print(f"已打开链接: {url}")
                    except Exception as e2:
                        print(f"无法打开链接: {url}, 错误: {e2}")
            else:
                print("该热搜项目没有可用的链接")
                
        super().mouseDoubleClickEvent(event)
        
    def reset_click_state(self):
        """恢复点击状态"""
        self.is_clicked = False
        self.update()
    
    def paintEvent(self, event):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置背景颜色
        background_color = QColor(255, 255, 255)  # 白色背景
        if self.underMouse():
            background_color = QColor(245, 246, 247)  # 悬停时的浅灰色
        
        # 先绘制圆角背景
        painter.setBrush(QBrush(background_color))
        painter.setPen(Qt.NoPen)  # 不要边框，先只绘制背景
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # 然后绘制边框
        pen = QPen(QColor(233, 236, 239))  # 浅灰色边框
        if self.is_clicked:
            pen.setColor(QColor(40, 167, 69))  # 点击时的绿色边框
            pen.setWidth(2)
        else:
            pen.setWidth(1)
        
        painter.setBrush(Qt.NoBrush)  # 不要填充，只绘制边框
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)
        
        super().paintEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.update()
        super().leaveEvent(event)


class PlatformTabWidget(QWidget):
    """单个平台的Tab页面"""
    
    def __init__(self, platform_name: str, api_instance, parent=None):
        super().__init__(parent)
        self.platform_name = platform_name
        self.api_instance = api_instance
        self.hotspots_data = []
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # 加载页面
        self.loading_widget = self.create_loading_widget()
        self.stacked_widget.addWidget(self.loading_widget)
        
        # 内容页面
        self.content_widget = self.create_content_widget()
        self.stacked_widget.addWidget(self.content_widget)
        
        # 错误页面
        self.error_widget = self.create_error_widget()
        self.stacked_widget.addWidget(self.error_widget)
        
        # 默认显示加载页面
        self.show_loading()
        
    def create_loading_widget(self) -> QWidget:
        """创建加载页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # 加载图标
        loading_label = QLabel("🔄")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: #007bff;
                padding: 20px;
            }
        """)
        
        # 加载文字
        text_label = QLabel(f"正在加载{self.platform_name}热搜...")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                padding: 10px;
            }
        """)
        
        layout.addWidget(loading_label)
        layout.addWidget(text_label)
        
        return widget
        
    def create_content_widget(self) -> QWidget:
        """创建内容页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
                background-color: #808080;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        # 热搜列表容器
        self.hotspots_container = QWidget()
        self.hotspots_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        self.hotspots_container.setAutoFillBackground(False)
        self.hotspots_layout = QVBoxLayout(self.hotspots_container)
        self.hotspots_layout.setContentsMargins(0, 6, 8, 8)
        self.hotspots_layout.setSpacing(6)
        
        scroll_area.setWidget(self.hotspots_container)
        layout.addWidget(scroll_area)
        
        return widget
        
    def create_error_widget(self) -> QWidget:
        """创建错误页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # 错误图标
        error_label = QLabel("❌")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: #dc3545;
                padding: 20px;
            }
        """)
        
        # 错误文字
        self.error_text_label = QLabel("加载失败")
        self.error_text_label.setAlignment(Qt.AlignCenter)
        self.error_text_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                padding: 10px;
            }
        """)
        
        # 重试按钮
        retry_button = QPushButton("重试")
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        retry_button.clicked.connect(self.retry_loading)
        
        layout.addWidget(error_label)
        layout.addWidget(self.error_text_label)
        layout.addWidget(retry_button)
        
        return widget
        
    def show_loading(self):
        """显示加载状态"""
        self.stacked_widget.setCurrentIndex(0)
        
    def show_content(self):
        """显示内容"""
        self.stacked_widget.setCurrentIndex(1)
        
    def show_error(self, error_message: str):
        """显示错误状态"""
        self.error_text_label.setText(f"加载{self.platform_name}热搜失败\n{error_message}")
        self.stacked_widget.setCurrentIndex(2)
        
    def update_hotspots(self, hotspots: List[Dict]):
        """更新热搜数据"""
        self.hotspots_data = hotspots
        
        # 清空现有项目
        while self.hotspots_layout.count():
            child = self.hotspots_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 添加新项目
        for hotspot in hotspots:
            item_widget = HotspotItemWidget(hotspot)
            self.hotspots_layout.addWidget(item_widget)
            
        # 添加弹性空间
        self.hotspots_layout.addStretch()
        
        # 显示内容
        self.show_content()
        
    def retry_loading(self):
        """重试加载"""
        self.show_loading()
        # 发送重试信号给父组件
        parent_widget = self.parent()
        while parent_widget and not isinstance(parent_widget, HotspotCard):
            parent_widget = parent_widget.parent()
        if parent_widget:
            parent_widget.fetch_platform_data(self.platform_name)


class HotspotCard(SidebarWidget):
    """多平台热搜侧边栏组件"""
    
    name = '热搜榜'
    category = '资讯'
    description = '实时获取知乎、抖音、Bilibili、今日头条、微博热搜榜单'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置组件尺寸
        self.setMinimumWidth(250)
        self.resize(400, 500)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 初始化API实例
        self.apis = {
            '微博': WeiboHotspotAPI(),
            '今日头条': ToutiaoHotspotAPI(),
            'Bilibili': BilibiliHotspotAPI(),
            '抖音': DouyinHotspotAPI(),
        }
        
        # 数据获取线程
        self.data_threads = {}
        
        # 初始化UI
        self.setup_ui()
        
        # 设置定时器，每5分钟自动刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(5 * 60 * 1000)  # 5分钟
        
        # 初始加载数据
        self.refresh_all_data()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 设置主组件背景为透明
        self.setStyleSheet("""
            HotspotCard {
                background-color: transparent;
            }
        """)
        
        # 创建Tab组件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                height: 20px;
                background-color: #f8f9fa;
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 4px 4px 0 0;
                font-size: 12px;
                color: #666;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
        """)
        
        # 添加各平台Tab页面
        for platform_name, api_instance in self.apis.items():
            tab_widget = PlatformTabWidget(platform_name, api_instance)
            self.tab_widget.addTab(tab_widget, platform_name)
            
        layout.addWidget(self.tab_widget)
        
    def fetch_platform_data(self, platform_name: str):
        """获取指定平台的数据"""
        if platform_name in self.data_threads:
            # 如果线程还在运行，先停止
            if self.data_threads[platform_name].isRunning():
                self.data_threads[platform_name].quit()
                self.data_threads[platform_name].wait()
                
        # 创建新线程
        api_instance = self.apis[platform_name]
        thread = HotspotDataThread(platform_name, api_instance, 20)
        thread.data_fetched.connect(self.on_data_fetched)
        thread.error_occurred.connect(self.on_error_occurred)
        
        self.data_threads[platform_name] = thread
        thread.start()
        
    def refresh_all_data(self):
        """刷新所有平台数据"""
        for platform_name in self.apis.keys():
            self.fetch_platform_data(platform_name)
            
    def on_data_fetched(self, platform_name: str, hotspots: List[Dict]):
        """数据获取成功回调"""
        # 找到对应的Tab页面并更新数据
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if tab_widget.platform_name == platform_name:
                tab_widget.update_hotspots(hotspots)
                break
                
    def on_error_occurred(self, platform_name: str, error_message: str):
        """数据获取失败回调"""
        # 找到对应的Tab页面并显示错误
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if tab_widget.platform_name == platform_name:
                tab_widget.show_error(error_message)
                break
                
    def get_config(self) -> Dict:
        """获取配置"""
        return {
            'refresh_interval': 5  # 刷新间隔（分钟）
        }
        
    def set_config(self, config: Dict):
        """设置配置"""
        refresh_interval = config.get('refresh_interval', 5)
        self.refresh_timer.setInterval(refresh_interval * 60 * 1000)
        
    def closeEvent(self, event):
        """关闭事件"""
        # 停止所有线程
        for thread in self.data_threads.values():
            if thread.isRunning():
                thread.quit()
                thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    hotspot_card = HotspotCard()
    hotspot_card.show()
    
    sys.exit(app.exec_())
