from PySide2 import QtWidgets, QtCore, QtGui
import requests
import qtawesome

request_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


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


class SoftwareEditDialog(QtWidgets.QDialog):
    """软件项目编辑对话框"""

    def __init__(self, name="", path="", icon_path="", item_type="file", parent=None):
        super().__init__(parent)
        self.name = name
        self.path = path
        self.icon_path = icon_path
        self.item_type = item_type
        self.selected_icon = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("编辑软件信息")
        self.setFixedSize(400, 350)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 12px;
                color: #333;
                font-weight: bold;
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
            QPushButton#cancelBtn {
                background-color: #6c757d;
            }
            QPushButton#cancelBtn:hover {
                background-color: #545b62;
            }
            QPushButton#browseBtn {
                background-color: #28a745;
                padding: 6px 12px;
            }
            QPushButton#browseBtn:hover {
                background-color: #218838;
            }
            QPushButton#iconBtn {
                background-color: #17a2b8;
                padding: 6px 12px;
            }
            QPushButton#iconBtn:hover {
                background-color: #138496;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QtWidgets.QLabel("编辑软件信息")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        # 图标预览
        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.setSpacing(10)

        icon_preview_label = QtWidgets.QLabel("图标:")
        icon_layout.addWidget(icon_preview_label)

        self.icon_preview = QtWidgets.QLabel()
        self.icon_preview.setFixedSize(40, 40)
        self.icon_preview.setStyleSheet("border: 1px solid #ddd; border-radius: 4px;")
        self.icon_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.load_icon_preview()
        icon_layout.addWidget(self.icon_preview)

        choose_icon_btn = QtWidgets.QPushButton("选择图标")
        choose_icon_btn.setObjectName("iconBtn")
        choose_icon_btn.clicked.connect(self.choose_icon)
        icon_layout.addWidget(choose_icon_btn)

        icon_layout.addStretch()
        layout.addLayout(icon_layout)

        # 名称输入
        name_label = QtWidgets.QLabel("名称:")
        layout.addWidget(name_label)

        self.name_input = QtWidgets.QLineEdit(self.name)
        layout.addWidget(self.name_input)

        # 路径输入
        path_label = QtWidgets.QLabel("路径:" if self.item_type == "file" else "网址:")
        layout.addWidget(path_label)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.setSpacing(8)

        self.path_input = QtWidgets.QLineEdit(self.path)
        path_layout.addWidget(self.path_input, 1)

        if self.item_type == "file":
            browse_btn = QtWidgets.QPushButton("浏览")
            browse_btn.setObjectName("browseBtn")
            browse_btn.clicked.connect(self.browse_file)
            path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        # 类型显示
        type_label = QtWidgets.QLabel(f"类型: {'文件' if self.item_type == 'file' else '网站'}")
        type_label.setStyleSheet("color: #666; font-weight: normal;")
        layout.addWidget(type_label)

        layout.addStretch()

        # 按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QtWidgets.QPushButton("取消")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QtWidgets.QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def load_icon_preview(self):
        """加载图标预览"""
        try:
            if self.item_type == "website" and self.icon_path:
                # 网站图标
                icon = self._load_icon_from_http(self.icon_path)
            elif self.item_type == "file" and self.icon_path:
                # 文件图标
                icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(self.icon_path))
            else:
                # 默认图标
                icon = qtawesome.icon('fa5s.question')

            pixmap = icon.pixmap(40, 40)
            self.icon_preview.setPixmap(pixmap)
        except:
            # 加载失败时使用默认图标
            icon = qtawesome.icon('fa5s.question')
            pixmap = icon.pixmap(40, 40)
            self.icon_preview.setPixmap(pixmap)

    def _load_icon_from_http(self, url):
        """从网络加载图标"""
        if not url:
            return qtawesome.icon('msc.browser')
        try:
            response = requests.get(url, headers=request_headers, timeout=3)
            response.raise_for_status()
            data = QtCore.QByteArray(response.content)
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            return QtGui.QIcon(pixmap)
        except:
            return qtawesome.icon('fa5s.browser')

    def choose_icon(self):
        """选择图标"""
        if self.item_type == "file":
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "选择图标文件", "",
                "图标文件 (*.ico *.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
            )
            if file_path:
                self.selected_icon = file_path
                try:
                    pixmap = QtGui.QPixmap(file_path).scaled(40, 40, QtCore.Qt.KeepAspectRatio,
                                                             QtCore.Qt.SmoothTransformation)
                    self.icon_preview.setPixmap(pixmap)
                except:
                    QtWidgets.QMessageBox.warning(self, "错误", "无法加载选中的图标文件")
        else:
            # 网站类型，让用户输入图标URL
            url, ok = QtWidgets.QInputDialog.getText(self, "输入图标URL", "请输入图标的网址:")
            if ok and url.strip():
                self.selected_icon = url.strip()
                try:
                    icon = self._load_icon_from_http(url.strip())
                    pixmap = icon.pixmap(40, 40)
                    self.icon_preview.setPixmap(pixmap)
                except:
                    QtWidgets.QMessageBox.warning(self, "错误", "无法加载图标URL")

    def browse_file(self):
        """浏览文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择程序文件", "",
            "可执行文件 (*.exe);;快捷方式 (*.lnk);;所有文件 (*.*)"
        )
        if file_path:
            self.path_input.setText(file_path)

    def get_data(self):
        """获取编辑后的数据"""
        return {
            'name': self.name_input.text().strip(),
            'path': self.path_input.text().strip(),
            'icon': self.selected_icon or self.icon_path,
            'type': self.item_type
        }

