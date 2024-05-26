import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import qfluentwidgets
from qfluentwidgets import FluentIcon
from qframelesswindow import FramelessWindow

from fingertips.settings.config_model import config_model
from fingertips.chat.widgets import ChatHistoryWidget


def is_win11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class ChatListCard(qfluentwidgets.CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_chat = qfluentwidgets.PrimaryPushButton('新的聊天', self)
        self.chats_widget = qfluentwidgets.ListWidget()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        layout.addWidget(self.add_chat)
        layout.addWidget(self.chats_widget)


class ChatContentCard(qfluentwidgets.CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.chat_history_widget = ChatHistoryWidget(self)
        self.chat_history_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.chat_history_widget.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)

        self.setting_button = qfluentwidgets.ToolButton(FluentIcon.SETTING, self)
        self.upload_button = qfluentwidgets.ToolButton(FluentIcon.PHOTO, self)
        self.model_combobox = qfluentwidgets.ComboBox()
        self.model_combobox.addItems(config_model.openai_models.value)
        self.model_combobox.setCurrentText(config_model.openai_current_model.value)
        self.send_button = qfluentwidgets.PrimaryPushButton('发送', self)

        self.input_text = qfluentwidgets.TextEdit(self)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.setting_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.model_combobox)
        button_layout.addSpacerItem(QtWidgets.QSpacerItem(
            10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        ))
        button_layout.addWidget(self.send_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.chat_history_widget, 12)
        layout.addLayout(button_layout)
        layout.addWidget(self.input_text, 2)

        self.send_button.clicked.connect(self.send_button_clicked)

    def resizeEvent(self, event):
        self.chat_history_widget.apply_rounded_corners()

    def send_button_clicked(self):
        text = self.input_text.toPlainText()
        self.chat_history_widget.set_user_content(text)


class ChatWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.resize(1600, 900)
        self.setTitleBar(qfluentwidgets.FluentTitleBar(self))
        self.titleBar.raise_()
        self.setWindowTitle('Chat Window')
        self.setObjectName('LoginWindow')

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=qfluentwidgets.isDarkTheme())

        if not is_win11():
            color = (QtGui.QColor(25, 33, 42)
                     if qfluentwidgets.isDarkTheme()
                     else QtGui.QColor(240, 244, 249))
            self.setStyleSheet(f"#LoginWindow{{background: {color.name()}}}")

        self.chat_card = ChatListCard(self)
        self.chat_content_card = ChatContentCard(self)

        splitter = QtWidgets.QSplitter(QtGui.Qt.Horizontal)
        splitter.addWidget(self.chat_card)
        splitter.addWidget(self.chat_content_card)
        splitter.setSizes([200, 800])

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 46, 6, 6)
        layout.addWidget(splitter)


if __name__ == '__main__':
    import os
    from PySide2.QtWebEngineWidgets import QWebEngineView
    from PySide2 import QtGui

    os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9999'
    app = QtWidgets.QApplication([])

    cw = ChatWindow()
    cw.show()

    # 打开调试页面
    dw = QWebEngineView()
    dw.setWindowTitle('开发人员工具')
    dw.load(QtCore.QUrl('http://127.0.0.1:9999'))
    dw.move(600, 100)
    dw.show()

    app.exec_()
