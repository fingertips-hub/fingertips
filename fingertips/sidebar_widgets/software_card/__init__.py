from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget
from fingertips.sidebar_widgets.software_card.tab_widget import CustomTabBar
from fingertips.sidebar_widgets.software_card.content_widget import SoftwareListWidget
from fingertips.sidebar_widgets.software_card.widgets import ConfirmDialog, RenameDialog


class SoftwareCard(SidebarWidget):
    name = '软件盒子'
    category = '生活'

    # 信号定义
    tab_renamed = QtCore.Signal(int, str)  # 标签页重命名信号

    def __init__(self, show_add_button=True, parent=None):
        super().__init__(parent)
        self.tab_counter = 1

        self.setMinimumHeight(200)
        # 设置透明
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 创建主布局
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 创建标签栏
        self.tab_bar = CustomTabBar(show_add_button, self)
        self.layout.addWidget(self.tab_bar)

        # 创建内容区域
        self.content_area = QtWidgets.QStackedWidget()
        self.content_area.setStyleSheet("""
            QStackedWidget {
                border: 1px solid #fff;
                background-color: white;
                margin: 0px;
                padding: 0px;
            }
        """)
        self.layout.addWidget(self.content_area)

        # 设置拉伸策略：标签栏固定高度，内容区域占用剩余空间
        self.layout.setStretchFactor(self.tab_bar, 0)  # 标签栏不拉伸
        self.layout.setStretchFactor(self.content_area, 1)  # 内容区域占用所有剩余空间

        # 连接信号
        self.tab_bar.tab_changed.connect(self._on_tab_changed)
        self.tab_bar.tab_close_requested.connect(self._on_tab_close_requested)
        self.tab_bar.tab_rename_requested.connect(self._on_tab_rename_requested)
        self.tab_bar.tab_moved.connect(self._on_tab_moved)  # 连接标签页移动信号
        self.tab_bar.tab_dragged.connect(self._on_tab_dragged)
        if show_add_button:
            self.tab_bar.add_tab_requested.connect(self.add_tab_content)

        # 启用鼠标滚轮事件
        self.setMouseTracking(True)

    def add_tab(self, widget, text, closable=True):
        """添加标签页 - 主要API接口"""
        # 添加到内容区域
        index = self.content_area.addWidget(widget)

        # 添加到标签栏
        tab_index = self.tab_bar.add_tab(text, closable)

        return tab_index

    def remove_tab(self, index):
        # 从内容区域移除
        widget = self.content_area.widget(index)
        self.content_area.removeWidget(widget)
        if widget:
            widget.deleteLater()

        # 从标签栏移除
        self.tab_bar.remove_tab(index)
        return True

    def edit_mode_changed(self, edit_mode):
        self.edit_mode = edit_mode

    def _on_tab_dragged(self, start_index, end_index):
        self.save_config_signal.emit()

    def on_content_widget_changed(self):
        self.save_config_signal.emit()

    def _connect_content_widget_signals(self, content_widget):
        """连接SoftwareListWidget的所有信号到保存配置方法"""
        content_widget.item_added.connect(self.on_content_widget_changed)
        content_widget.item_removed.connect(self.on_content_widget_changed)
        content_widget.item_renamed.connect(self.on_content_widget_changed)
        content_widget.item_updated.connect(self.on_content_widget_changed)

    def add_tab_content(self):
        """添加默认标签页 - 可重写此方法自定义默认内容"""
        # 创建默认标签页内容
        content_widget = SoftwareListWidget(self.get_dialog_parent())
        self._connect_content_widget_signals(content_widget)

        # 添加标签页
        tab_name = f"Tab {self.tab_counter}"
        index = self.add_tab(content_widget, tab_name)

        # 切换到新标签页
        self.set_current_index(index)

        # 增加计数器
        self.tab_counter += 1

        return index

    def set_current_index(self, index):
        """设置当前标签页"""
        self.tab_bar.set_current_index(index)

    def get_current_index(self):
        """获取当前标签页索引"""
        return self.tab_bar.get_current_index()

    def count(self):
        """获取标签页数量"""
        return self.tab_bar.count()

    def widget(self, index):
        """获取指定索引的组件"""
        return self.content_area.widget(index)

    def current_widget(self):
        """获取当前显示的组件"""
        return self.content_area.currentWidget()

    def tab_text(self, index):
        """获取标签页文本"""
        return self.tab_bar.tab_text(index)

    def set_tab_text(self, index, text):
        """设置标签页文本"""
        self.tab_bar.set_tab_text(index, text)

    def _on_tab_changed(self, index):
        """内部标签页切换处理"""
        self.content_area.setCurrentIndex(index)

    def _on_tab_close_requested(self, index):
        """内部标签页关闭请求处理"""
        # 获取标签页名称
        tab_name = self.tab_text(index)

        # 显示确认对话框
        if ConfirmDialog.show_confirm(
                title="确认删除",
                message=f"您确定要删除标签页 '{tab_name}' 吗？\n\n此操作无法撤销。",
                parent=None
        ):
            self.remove_tab(index)
            self.save_config_signal.emit()

    def _on_tab_rename_requested(self, index, old_name):
        """内部标签页重命名请求处理"""
        new_text, ok = RenameDialog.get_new_name(old_name)
        if ok and new_text and new_text != old_name:
            self.tab_bar.set_tab_text(index, new_text)
            self.save_config_signal.emit()

    def get_config(self):
        """获取软件卡片的完整配置信息，返回可序列化的字典
        
        Returns:
            dict: 包含所有标签页和软件信息的配置字典，格式如下：
            {
                'current_tab_index': int,  # 当前选中的标签页索引
                'tab_counter': int,        # 标签页计数器
                'tabs': [
                    {
                        'name': str,           # 标签页名称
                        'closable': bool,      # 是否可关闭
                        'software_list': [     # 软件列表
                            {
                                'name': str,
                                'path': str,
                                'type': str,
                                'icon': str
                            },
                            ...
                        ]
                    },
                    ...
                ]
            }
        """
        config = {
            'current_tab_index': self.get_current_index(),
            'tab_counter': self.tab_counter,
            'tabs': []
        }
        
        # 遍历所有标签页
        for i in range(self.count()):
            tab_info = {
                'name': self.tab_text(i),
                'closable': self.tab_bar.is_tab_closable(i) if hasattr(self.tab_bar, 'is_tab_closable') else True,
                'software_list': []
            }
            
            # 获取标签页内容
            widget = self.widget(i)
            if isinstance(widget, SoftwareListWidget):
                # 获取软件列表信息
                tab_info['software_list'] = widget.get_all_items_info()
            
            config['tabs'].append(tab_info)
        
        return config
    
    def _on_tab_moved(self, from_index, to_index):
        """内部标签页移动处理 - 同步移动内容区域中的widget"""
        if from_index == to_index or from_index < 0 or to_index < 0:
            return
            
        if from_index >= self.content_area.count() or to_index >= self.content_area.count():
            return
        
        # 获取要移动的widget
        widget = self.content_area.widget(from_index)
        if widget is None:
            return
        
        # 从原位置移除widget（但不删除）
        self.content_area.removeWidget(widget)
        
        # 将widget插入到新位置
        self.content_area.insertWidget(to_index, widget)
        
        # 移动完成后，确保content_area的当前索引与tab_bar的当前索引保持同步
        # CustomTabBar的move_tab方法已经正确处理了标签栏的当前索引更新
        tab_current_index = self.tab_bar.get_current_index()
        self.content_area.setCurrentIndex(tab_current_index)

        self.save_config_signal.emit()

    def load_config(self, config):
        """从配置字典中加载软件卡片状态
        
        Args:
            config (dict): 配置字典，格式与 get_config() 返回值相同
        """
        if not isinstance(config, dict):
            return False
        
        try:
            # 清空现有标签页
            while self.count() > 0:
                self.remove_tab(0)
            
            # 恢复标签页计数器
            self.tab_counter = config.get('tab_counter', 1)
            
            # 创建标签页
            tabs_data = config.get('tabs', [])
            for tab_data in tabs_data:
                tab_name = tab_data.get('name', 'Tab')
                closable = tab_data.get('closable', True)
                software_list = tab_data.get('software_list', [])
                
                # 创建软件列表组件
                content_widget = SoftwareListWidget(self.get_dialog_parent())
                
                # 连接信号到保存配置方法
                self._connect_content_widget_signals(content_widget)
                
                # 加载软件列表
                if software_list:
                    content_widget.load_items_from_info(software_list)
                
                # 添加标签页
                self.add_tab(content_widget, tab_name, closable)
            
            # 恢复当前选中的标签页
            current_index = config.get('current_tab_index', 0)
            if 0 <= current_index < self.count():
                self.set_current_index(current_index)
            
            return True
            
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False

    def set_config(self, config):
        self.load_config(config)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = SoftwareCard()
    w.show()
    app.exec_()
