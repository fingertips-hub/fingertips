from PySide2 import QtWidgets, QtCore


class RenameDialog(QtWidgets.QDialog):
    """自定义重命名对话框 - 美观的重命名界面"""

    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("重命名标签页")
        self.setFixedSize(300, 150)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
                selection-background-color: #4a9eff;
            }
            QLineEdit:focus {
                border-color: #4a9eff;
                outline: none;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                color: #333;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton#ok_button {
                background-color: #4a9eff;
                border-color: #4a9eff;
                color: white;
            }
            QPushButton#ok_button:hover {
                background-color: #357abd;
                border-color: #357abd;
            }
            QPushButton#ok_button:pressed {
                background-color: #2968a3;
            }
            QPushButton#ok_button:disabled {
                background-color: #cccccc;
                border-color: #cccccc;
                color: #666666;
            }
        """)

        # 创建布局
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题标签
        title_label = QtWidgets.QLabel("请输入新的标签页名称:")
        layout.addWidget(title_label)

        # 输入框
        self.line_edit = QtWidgets.QLineEdit(current_name)
        self.line_edit.selectAll()  # 选中所有文本
        layout.addWidget(self.line_edit)

        # 按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        # 取消按钮
        self.cancel_button = QtWidgets.QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        # 确定按钮
        self.ok_button = QtWidgets.QPushButton("确定")
        self.ok_button.setObjectName("ok_button")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)  # 设为默认按钮
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        # 连接信号
        self.line_edit.textChanged.connect(self.on_text_changed)
        self.line_edit.returnPressed.connect(self.accept)  # 回车确认

        # 初始状态检查
        self.on_text_changed(current_name)

        # 设置焦点
        self.line_edit.setFocus()

    def on_text_changed(self, text):
        """文本改变时的处理"""
        # 只有当文本不为空且去除空格后不为空时才启用确定按钮
        self.ok_button.setEnabled(bool(text.strip()))

    def get_text(self):
        """获取输入的文本"""
        return self.line_edit.text().strip()

    @staticmethod
    def get_new_name(current_name, parent=None):
        """静态方法，类似QInputDialog.getText的使用方式"""
        dialog = RenameDialog(current_name, parent)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            return dialog.get_text(), True
        else:
            return "", False


class ConfirmDialog(QtWidgets.QDialog):
    """自定义确认对话框 - 美观的确认界面"""

    def __init__(self, title="确认操作", message="您确定要执行此操作吗？", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(320, 160)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        # 设置对话框样式（与RenameDialog保持一致）
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#message_label {
                color: #555;
                font-weight: normal;
                line-height: 1.4;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                color: #333;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton#ok_button {
                background-color: #dc3545;
                border-color: #dc3545;
                color: white;
            }
            QPushButton#ok_button:hover {
                background-color: #c82333;
                border-color: #bd2130;
            }
            QPushButton#ok_button:pressed {
                background-color: #bd2130;
            }
        """)

        # 创建布局
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题标签
        title_label = QtWidgets.QLabel(title)
        layout.addWidget(title_label)

        # 消息标签
        self.message_label = QtWidgets.QLabel(message)
        self.message_label.setObjectName("message_label")
        self.message_label.setWordWrap(True)  # 允许文本换行
        layout.addWidget(self.message_label)

        # 按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        # 取消按钮
        self.cancel_button = QtWidgets.QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        # 确定按钮
        self.ok_button = QtWidgets.QPushButton("确定")
        self.ok_button.setObjectName("ok_button")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)  # 设为默认按钮
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        # 设置焦点到取消按钮（安全起见）
        self.cancel_button.setFocus()

    @staticmethod
    def show_confirm(title="确认操作", message="您确定要执行此操作吗？", parent=None):
        """静态方法，显示确认对话框并返回用户选择"""
        dialog = ConfirmDialog(title, message, parent)
        return dialog.exec_() == QtWidgets.QDialog.Accepted
