import sys
import requests
from PySide2.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                               QStackedWidget, QComboBox, QFormLayout, QSizePolicy)
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget


PROXIES = {"http": None, "https": None}


class HitokotoCard(SidebarWidget):
    """美观优雅的一言组件"""
    name = '一言'
    category = '生活'

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        # 设置最小尺寸
        self.resize(400, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 设置窗口属性
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        # 初始化配置
        self.sentence_type = 'j'  # 默认为网易云音乐类型
        
        # 初始化数据
        self.hitokoto_data = {
            'hitokoto': '正在获取一言...',
            'from_who': '',
            'from': '',
            'type': '',
            'uuid': ''
        }
        
        # 防止重复刷新
        self.is_refreshing = False
        
        # 句子类型映射
        self.sentence_types = {
            'a': '动画',
            'b': '漫画', 
            'c': '游戏',
            'd': '文学',
            'e': '原创',
            'f': '来自网络',
            'g': '其他',
            'h': '影视',
            'i': '诗词',
            'j': '网易云',
            'k': '哲学',
            'l': '抖机灵'
        }
        
        # 初始化UI
        self.setup_ui()
        
        # 初始化数据获取
        self.refresh_content()
        
        # 设置双击事件
        self.mouseDoubleClickEvent = self.on_double_click

    def setup_ui(self):
        """设置用户界面"""
        # 创建堆叠窗口管理器
        self.stacked_widget = QStackedWidget()
        
        # 创建主显示页面
        self.main_page = self.create_main_page()
        self.stacked_widget.addWidget(self.main_page)
        
        # 创建配置页面
        self.config_page = self.create_config_page()
        self.stacked_widget.addWidget(self.config_page)
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

    def create_main_page(self):
        """创建主显示页面"""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 名言内容标签
        self.hitokoto_label = QLabel()
        self.hitokoto_label.setWordWrap(True)
        self.hitokoto_label.setAlignment(Qt.AlignCenter)
        self.hitokoto_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #fff;
                background-color: transparent;
                padding: 10px;
                line-height: 1.6;
            }
        """)

        hitokoto_font = QFont("Segoe UI", 38, QFont.Bold)
        hitokoto_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        self.hitokoto_label.setFont(hitokoto_font)
        
        # 作者信息标签
        self.author_label = QLabel()
        self.author_label.setAlignment(Qt.AlignCenter)
        self.author_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #eee;
                background-color: transparent;
                padding: 5px;
                font-style: italic;
            }
        """)
        
        # 添加到主布局
        layout.addStretch()
        layout.addWidget(self.hitokoto_label)
        layout.addWidget(self.author_label)
        layout.addStretch()
        
        page.setLayout(layout)
        return page

    def create_config_page(self):
        """创建配置页面"""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 8px;
            }
        """)
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)
        
        # 设置表单标签颜色
        page.setStyleSheet(page.styleSheet() + """
            QFormLayout QLabel {
                color: #333333;
                font-size: 14px;
            }
        """)
        
        # 句子类型选择
        self.type_combo = QComboBox()
        for key, value in self.sentence_types.items():
            self.type_combo.addItem(value, key)
        
        # 设置当前选择
        current_index = list(self.sentence_types.keys()).index(self.sentence_type)
        self.type_combo.setCurrentIndex(current_index)

        self.type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                color: #333333;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                color: #333333;
                background-color: white;
                border: 1px solid #bdc3c7;
            }
        """)

        # 添加到表单
        form_layout.addRow('句子类型:', self.type_combo)

        page.setLayout(form_layout)
        return page

    def get_hitokoto(self):
        """获取一言数据"""
        try:
            url = f'https://v1.hitokoto.cn/?c={self.sentence_type}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            }
            response = requests.get(url, headers=headers, proxies=PROXIES, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'hitokoto': data.get('hitokoto', ''),
                'from_who': data.get('from_who', ''),
                'from': data.get('from', ''),
                'type': data.get('type', ''),
                'uuid': data.get('uuid', '')
            }
        except Exception as e:
            print(f"获取一言数据失败: {e}")
            return {
                'hitokoto': '获取一言失败，请稍后重试',
                'from_who': '系统提示',
                'from': '错误信息'
            }

    def on_double_click(self, event):
        """双击事件处理"""
        if not self.edit_mode:
            self.refresh_content()
        super().mouseDoubleClickEvent(event)

    def refresh_content(self):
        """刷新内容"""

        # 防止重复刷新
        if self.is_refreshing:
            return
        
        self.is_refreshing = True
        
        # 立即清空并设置加载状态
        self.hitokoto_label.clear()
        self.author_label.clear()
        self.hitokoto_label.setText('正在获取一言...')
        self.author_label.setText('')
        
        # 直接获取一言数据
        self.hitokoto_data = self.get_hitokoto()
        self.update_hitokoto_display()
        
        # 重置刷新状态
        self.is_refreshing = False

    def update_hitokoto_display(self):
        """更新一言显示"""
        hitokoto = self.hitokoto_data.get('hitokoto', '')
        from_who = self.hitokoto_data.get('from_who', '')
        
        # 先清空标签
        self.hitokoto_label.clear()
        self.author_label.clear()
        
        # 更新标签内容
        self.hitokoto_label.setText(hitokoto)
        
        # 构建作者信息
        author_text = ''
        if from_who:
            author_text = f'—— {from_who}'
        
        self.author_label.setText(author_text)

    def edit_mode_changed(self, edit_mode):
        """编辑模式变更"""
        super().edit_mode_changed(edit_mode)
        
        if edit_mode:
            self.stacked_widget.setCurrentIndex(1)  # 显示配置页面
            # 更新配置页面的选择（临时断开信号避免触发保存）
            current_index = list(self.sentence_types.keys()).index(self.sentence_type)
            self.type_combo.setCurrentIndex(current_index)
        else:
            self.stacked_widget.setCurrentIndex(0)  # 显示主页面
            self.refresh_content()  # 刷新内容

    def get_config(self):
        """获取配置"""
        self.sentence_type = self.type_combo.currentData()
        return {
            'sentence_type': self.sentence_type
        }

    def set_config(self, config):
        """设置配置"""
        self.sentence_type = config.get('sentence_type', 'j')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = HitokotoCard()
    widget.show()
    app.exec_()
