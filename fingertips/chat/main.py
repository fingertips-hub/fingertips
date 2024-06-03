import sys
import time
from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import qfluentwidgets
from qfluentwidgets import FluentIcon
from qframelesswindow import FramelessWindow
from qfluentwidgets import FluentTitleBar as _FluentTitleBar

from fingertips.settings.config_model import config_model
from fingertips.chat.widgets import ChatHistoryWidget, ChatListWidget
from fingertips.chat.settings_widget import ChatSettingDialog
from fingertips.widget_utils import signal_bus


def is_win11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class ChatListCard(qfluentwidgets.CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_chat = qfluentwidgets.PrimaryPushButton('新的聊天', self)
        self.chats_widget = ChatListWidget()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        layout.addWidget(self.add_chat)
        layout.addWidget(self.chats_widget)

        self.add_chat.clicked.connect(self.add_chat_clicked)

    def add_chat_clicked(self):
        self.chats_widget.add_item()


class ChatContentCard(qfluentwidgets.CardWidget):
    def __init__(self, chat_list_widget: ChatListWidget, parent=None):
        super().__init__(parent)
        self.is_send = False
        self.init_histories = []
        self.page_loaded = False
        self.chat_list_widget = chat_list_widget

        self.chat_history_widget = ChatHistoryWidget(self)
        self.chat_history_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                               QtWidgets.QSizePolicy.Expanding)
        self.chat_history_widget.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)

        self.upload_button = qfluentwidgets.ToolButton(FluentIcon.PHOTO, self)
        self.cut_button = qfluentwidgets.ToolButton(FluentIcon.CLIPPING_TOOL, self)
        self.model_combobox = qfluentwidgets.ComboBox()
        self.model_combobox.addItems(config_model.openai_models.value)
        self.model_combobox.setCurrentText(config_model.openai_current_model.value)

        self.resend_button = qfluentwidgets.ToolButton(FluentIcon.SYNC, self)
        self.send_button = qfluentwidgets.PrimaryPushButton('发送', self)
        self.send_button.setMinimumWidth(100)

        self.input_text = qfluentwidgets.PlainTextEdit(self)
        self.input_text.setPlaceholderText('按 Ctrl + Enter 发送')

        input_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('ctrl+return'), self)
        input_shortcut.activated.connect(self.send_button_clicked)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cut_button)
        button_layout.addWidget(self.model_combobox)
        button_layout.addSpacerItem(QtWidgets.QSpacerItem(
            10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        ))
        button_layout.addWidget(self.resend_button)
        button_layout.addWidget(self.send_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.chat_history_widget, 12)
        layout.addLayout(button_layout)
        layout.addWidget(self.input_text, 2)

        self.send_button.clicked.connect(self.send_button_clicked)
        self.chat_history_widget.chat_response_finished.connect(self.chat_finished)
        self.resend_button.clicked.connect(self.resend_button_clicked)
        self.model_combobox.currentTextChanged.connect(self.model_combobox_changed)
        signal_bus.chat_item_deleted.connect(
            self.chat_history_widget.bridge_object.clear_chat_histories)

        self.installEventFilter(self)

    def init_content(self, histories):
        self.chat_history_widget.init_content(histories)

    def model_combobox_changed(self):
        if self.chat_list_widget.current_chat_item:
            self.chat_list_widget.current_chat_item.chat_model.model.value = self.model_combobox.text()

    def set_current_model(self, model):
        self.model_combobox.setCurrentText(model)

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Return:
            if not self.input_text.hasFocus():
                self.input_text.setFocus()
                return True
        return super(ChatContentCard, self).eventFilter(source, event)

    def resend_button_clicked(self):
        if self.is_send:
            return self.chat_history_widget.stop_thread()

        if not self.chat_list_widget.current_chat_item:
            return qfluentwidgets.InfoBar.error(
                '错误', '请先开始一个聊天', duration=3000, parent=self)

        self.is_send = True
        self.chat_history_widget.set_user_content(
            chat_model=self.chat_list_widget.current_chat_item.chat_model,
            use_histories=True
        )
        self.send_button.setEnabled(False)
        self.input_text.setPlainText('')
        self.resend_button.setIcon(FluentIcon.PAUSE)

    def chat_finished(self):
        self.send_button.setEnabled(True)
        self.resend_button.setIcon(FluentIcon.SYNC)
        self.is_send = False

    def resizeEvent(self, event):
        self.chat_history_widget.apply_rounded_corners()

    def send_button_clicked(self):
        if self.is_send:
            return

        if not self.chat_list_widget.current_chat_item:
            return qfluentwidgets.InfoBar.error(
                '错误', '请先选择聊天或创建新的聊天', duration=2000, parent=self)

        text = self.input_text.toPlainText()
        if not text:
            return qfluentwidgets.InfoBar.error(
                '错误', '请先输入要提问的内容', duration=1500, parent=self)

        self.is_send = True
        item = self.chat_list_widget.current_chat_item
        self.chat_history_widget.set_user_content(text, item.chat_model)
        self.send_button.setEnabled(False)
        self.input_text.setPlainText('')
        self.resend_button.setIcon(FluentIcon.PAUSE)


class FluentTitleBar(_FluentTitleBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pin_button = qfluentwidgets.TransparentToggleToolButton(FluentIcon.PIN, self)
        self.pin_button.setChecked(config_model.chat_pin.value)
        self.buttonLayout.insertWidget(0, self.pin_button)


class ChatWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.resize(1200, 900)
        self.setTitleBar(FluentTitleBar(self))
        self.titleBar.raise_()
        self.setWindowTitle('聊天窗口')
        self.setObjectName('LoginWindow')

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=qfluentwidgets.isDarkTheme())
        qfluentwidgets.FluentStyleSheet.FLUENT_WINDOW.apply(self)

        if not is_win11():
            color = (QtGui.QColor(25, 33, 42)
                     if qfluentwidgets.isDarkTheme()
                     else QtGui.QColor(240, 244, 249))
            self.setStyleSheet(f"#LoginWindow{{background: {color.name()}}}")

        self.chat_card = ChatListCard(self)
        self.chat_content_card = ChatContentCard(self.chat_card.chats_widget, self)

        splitter = QtWidgets.QSplitter(QtGui.Qt.Horizontal)
        splitter.addWidget(self.chat_card)
        splitter.addWidget(self.chat_content_card)
        splitter.setSizes([200, 800])

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 46, 6, 6)
        layout.addWidget(splitter)

        signal_bus.chat_item_edited.connect(self.chat_item_edited)
        signal_bus.chat_item_clicked.connect(self._change_item)
        self.titleBar.pin_button.clicked.connect(self.toggle_topmost)

        self.is_init = True
        self.toggle_topmost(config_model.chat_pin.value)

    def toggle_topmost(self, topmost):
        if not topmost:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        qfluentwidgets.qconfig.set(config_model.chat_pin, topmost)
        if not self.is_init:
            return self.show()

        self.is_init = False

    def chat_item_edited(self, item):
        cssa = ChatSettingDialog(item.chat_model, self.parent())
        cssa.closed.connect(partial(self.chat_item_edit_close, item))
        cssa.show()

    def chat_item_edit_close(self, item):
        item.reset_title()
        if self.chat_card.chats_widget.current_chat_item == item:
            self._change_item(item)

    def _change_item(self, item):
        self.setWindowTitle(item.label.text())
        self.chat_content_card.set_current_model(item.chat_model.model.value)
        self.chat_content_card.init_content(item.chat_model.histories.value)

    def set_position(self):
        pos = QtWidgets.QDesktopWidget().availableGeometry().center()
        pos.setX(pos.x() - (self.width() / 2))
        pos.setY(pos.y() - (pos.y() - 80))
        self.move(pos)

    def show(self):
        if self.chat_card.chats_widget.current_chat_item:
            self._change_item(self.chat_card.chats_widget.current_chat_item)

        self.set_position()
        return super().show()


if __name__ == '__main__':
    import os
    from PySide2.QtWebEngineWidgets import QWebEngineView
    from PySide2 import QtGui

    # os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9999'
    app = QtWidgets.QApplication([])

    cw = ChatWindow()
    cw.show()

    # # 打开调试页面
    # dw = QWebEngineView()
    # dw.setWindowTitle('开发人员工具')
    # dw.load(QtCore.QUrl('http://127.0.0.1:9999'))
    # dw.move(600, 100)
    # dw.show()

    app.exec_()
