from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt
import qtawesome
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget


CHECKBOX_STYLE = '''
QCheckBox {
    font-size: 12px;
    color: #666;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #ccc;
    background-color: white;
}
QCheckBox::indicator:hover {
    border-color: #4CAF50;
}
QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border-color: #4CAF50;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05IDFMMy41IDYuNUwxIDQiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}
'''


class TodoItemWidget(QtWidgets.QWidget):
    """单个待办事项组件"""
    
    # 信号定义
    item_toggled = QtCore.Signal(bool)  # 完成状态切换信号
    item_deleted = QtCore.Signal()  # 删除信号
    item_edited = QtCore.Signal(str)  # 编辑信号
    
    def __init__(self, text="", completed=False, parent=None):
        super().__init__(parent)
        self.completed = completed
        self.original_text = text
        self.setup_ui()
        self.set_text(text)
        self.set_completed(completed)
        
    def setup_ui(self):
        """设置UI界面"""
        self.setFixedHeight(35)

        # 主布局
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 完成状态复选框
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setFixedSize(18, 18)
        self.checkbox.setStyleSheet(CHECKBOX_STYLE)
        self.checkbox.toggled.connect(self.on_toggle_completed)
        layout.addWidget(self.checkbox)
        
        # 任务文本标签
        self.text_label = QtWidgets.QLabel()
        self.text_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                background: transparent;
                border: none;
                padding: 4px;
            }
        """)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label, 1)
        
        # 任务文本编辑器（隐藏）
        self.text_editor = QtWidgets.QLineEdit()
        self.text_editor.setFixedHeight(26)
        self.text_editor.setStyleSheet("""
            QLineEdit {
                color: #333;
                font-size: 14px;
                background: transparent;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        self.text_editor.hide()
        self.text_editor.returnPressed.connect(self.finish_editing)
        self.text_editor.editingFinished.connect(self.finish_editing)
        layout.addWidget(self.text_editor, 1)
        
        # 删除按钮
        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setIcon(qtawesome.icon('fa.trash', color='#ff5722'))
        self.delete_button.setFixedSize(28, 28)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 14px;
                padding: 6px;
            }
            QPushButton:pressed {
                background-color: #ffcdd2;
            }
        """)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_button)
        
    def set_text(self, text):
        """设置任务文本"""
        self.original_text = text
        self.text_label.setText(text)
        self.text_editor.setText(text)
        self.update_appearance()
        
    def get_text(self):
        """获取任务文本"""
        return self.original_text
        
    def set_completed(self, completed):
        """设置完成状态"""
        self.completed = completed
        self.checkbox.setChecked(completed)
        self.update_appearance()
        
    def is_completed(self):
        """获取完成状态"""
        return self.completed
        
    def update_appearance(self):
        """更新外观（划线效果）"""
        if self.completed:
            # 完成状态：灰色文字 + 删除线
            self.text_label.setStyleSheet("""
                QLabel {
                    color: #888;
                    font-size: 14px;
                    background: transparent;
                    border: none;
                    padding: 4px;
                    text-decoration: line-through;
                }
            """)
        else:
            # 未完成状态：正常文字
            self.text_label.setStyleSheet("""
                QLabel {
                    color: #333;
                    font-size: 14px;
                    background: transparent;
                    border: none;
                    padding: 4px;
                }
            """)
    
    def on_toggle_completed(self, checked):
        """处理完成状态切换"""
        self.completed = checked
        self.update_appearance()
        self.item_toggled.emit(checked)
        
    def on_delete_clicked(self):
        """处理删除按钮点击"""
        self.item_deleted.emit()
        
    def mouseDoubleClickEvent(self, event):
        """双击开始编辑"""
        if event.button() == Qt.LeftButton and not self.completed:
            self.start_editing()
        super().mouseDoubleClickEvent(event)
        
    def start_editing(self):
        """开始编辑模式"""
        self.text_label.hide()
        self.text_editor.setText(self.original_text)
        self.text_editor.show()
        self.text_editor.setFocus()
        self.text_editor.selectAll()
        
    def finish_editing(self):
        """完成编辑"""
        new_text = self.text_editor.text().strip()
        if new_text and new_text != self.original_text:
            self.original_text = new_text
            self.text_label.setText(new_text)
            self.item_edited.emit(new_text)
        elif not new_text:
            # 如果文本为空，恢复原文本
            self.text_editor.setText(self.original_text)
            
        self.text_editor.hide()
        self.text_label.show()


class TodoListCard(SidebarWidget):
    """待办事项列表组件"""
    
    name = '待办清单'
    category = '生活'
    icon = 'fa.check-square'
    description = '管理你的待办事项，支持增删改查和完成状态管理'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.todos = []  # 存储所有待办事项数据
        self.show_only_uncompleted = False  # 是否仅显示未完成
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setMinimumSize(300, 120)
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
        main_layout.setSpacing(12)

        # 输入区域
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("输入新的待办事项...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 8px 10px;
                font-size: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                outline: none;
            }
        """)
        self.input_field.returnPressed.connect(self.add_todo)
        input_layout.addWidget(self.input_field, 1)
        
        self.add_button = QtWidgets.QPushButton()
        self.add_button.setIcon(qtawesome.icon('fa.plus', color='white'))
        self.add_button.setFixedSize(34, 34)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.add_button.clicked.connect(self.add_todo)
        input_layout.addWidget(self.add_button)
        
        main_layout.addLayout(input_layout)
        
        # 过滤选项
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        self.filter_checkbox = QtWidgets.QCheckBox("仅显示未完成")
        self.filter_checkbox.setStyleSheet(CHECKBOX_STYLE)
        self.filter_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_checkbox)

        # 统计信息
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888;
                background: transparent;
                border: none;
            }
        """)
        self.stats_label.setAlignment(Qt.AlignRight)
        filter_layout.addWidget(self.stats_label, 1)
        
        main_layout.addLayout(filter_layout)
        
        # 待办事项列表
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
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
        
        self.list_widget = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch()  # 添加弹性空间
        self.list_widget.setStyleSheet('border: none;')
        
        self.scroll_area.setWidget(self.list_widget)
        main_layout.addWidget(self.scroll_area, 1)
        
        # 更新统计信息
        self.update_stats()
        
    def add_todo(self):
        """添加新的待办事项"""
        text = self.input_field.text().strip()
        if not text:
            return
            
        # 创建待办事项数据
        todo_data = {
            'text': text,
            'completed': False,
            'id': len(self.todos)  # 简单的ID生成
        }
        self.todos.append(todo_data)
        
        # 创建UI组件
        self.create_todo_widget(todo_data)
        
        # 清空输入框
        self.input_field.clear()
        
        # 更新统计和保存配置
        self.update_stats()
        self.save_config_signal.emit()
        
    def create_todo_widget(self, todo_data):
        """创建待办事项UI组件"""
        todo_widget = TodoItemWidget(todo_data['text'], todo_data['completed'])
        
        # 连接信号
        todo_widget.item_toggled.connect(lambda checked, data=todo_data: self.on_todo_toggled(data, checked))
        todo_widget.item_deleted.connect(lambda data=todo_data: self.delete_todo(data))
        todo_widget.item_edited.connect(lambda text, data=todo_data: self.on_todo_edited(data, text))
        
        # 存储组件引用
        todo_data['widget'] = todo_widget
        
        # 添加到布局（在弹性空间之前）
        self.list_layout.insertWidget(self.list_layout.count() - 1, todo_widget)
        
        # 应用过滤
        self.apply_filter()
        
    def on_todo_toggled(self, todo_data, completed):
        """处理待办事项完成状态变化"""
        todo_data['completed'] = completed
        self.apply_filter()
        self.update_stats()
        self.save_config_signal.emit()
        
    def on_todo_edited(self, todo_data, new_text):
        """处理待办事项文本编辑"""
        todo_data['text'] = new_text
        self.save_config_signal.emit()
        
    def delete_todo(self, todo_data):
        """删除待办事项"""
        # 从数据列表中移除
        if todo_data in self.todos:
            self.todos.remove(todo_data)
            
        # 从UI中移除
        if 'widget' in todo_data:
            widget = todo_data['widget']
            self.list_layout.removeWidget(widget)
            widget.deleteLater()
            
        # 更新统计和保存配置
        self.update_stats()
        self.save_config_signal.emit()
        
    def on_filter_changed(self, checked):
        """处理过滤选项变化"""
        self.show_only_uncompleted = checked
        self.apply_filter()
        
    def apply_filter(self):
        """应用过滤条件"""
        for todo_data in self.todos:
            if 'widget' in todo_data:
                widget = todo_data['widget']
                if self.show_only_uncompleted:
                    # 仅显示未完成的
                    widget.setVisible(not todo_data['completed'])
                else:
                    # 显示所有
                    widget.setVisible(True)
                    
    def update_stats(self):
        """更新统计信息"""
        total = len(self.todos)
        completed = sum(1 for todo in self.todos if todo['completed'])
        uncompleted = total - completed
        
        self.stats_label.setText(f"已完成: {completed} | 待完成: {uncompleted}")
        
    def get_config(self):
        """获取配置信息"""
        return {
            'todos': [
                {
                    'text': todo['text'],
                    'completed': todo['completed'],
                    'id': todo['id']
                }
                for todo in self.todos
            ],
            'show_only_uncompleted': self.show_only_uncompleted
        }
        
    def set_config(self, config):
        """设置配置信息"""
        if not isinstance(config, dict):
            return
            
        # 清空现有数据
        self.clear_all_todos()
        
        # 加载待办事项
        todos_data = config.get('todos', [])
        for todo_data in todos_data:
            todo = {
                'text': todo_data.get('text', ''),
                'completed': todo_data.get('completed', False),
                'id': todo_data.get('id', len(self.todos))
            }
            self.todos.append(todo)
            self.create_todo_widget(todo)
            
        # 设置过滤选项
        self.show_only_uncompleted = config.get('show_only_uncompleted', False)
        self.filter_checkbox.setChecked(self.show_only_uncompleted)
        self.apply_filter()
        
        # 更新统计
        self.update_stats()
        
    def clear_all_todos(self):
        """清空所有待办事项"""
        for todo_data in self.todos[:]:
            if 'widget' in todo_data:
                widget = todo_data['widget']
                self.list_layout.removeWidget(widget)
                widget.deleteLater()
        self.todos.clear()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # 创建测试窗口
    window = QtWidgets.QMainWindow()
    todo_list = TodoListCard()
    window.setCentralWidget(todo_list)
    window.setWindowTitle("待办清单测试")
    window.resize(400, 600)
    
    window.show()
    sys.exit(app.exec_())
