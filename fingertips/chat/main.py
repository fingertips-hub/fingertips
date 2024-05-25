import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import qfluentwidgets
from qframelesswindow import FramelessWindow


def isWin11():
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

        self.input_text = qfluentwidgets.TextEdit(self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.input_text)


class ChatWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.resize(1000, 850)
        self.setTitleBar(qfluentwidgets.FluentTitleBar(self))
        self.titleBar.raise_()
        self.setWindowTitle('Chat Window')
        self.setObjectName('LoginWindow')

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=qfluentwidgets.isDarkTheme())

        if not isWin11():
            color = (QtGui.QColor(25, 33, 42)
                     if qfluentwidgets.isDarkTheme()
                     else QtGui.QColor(240, 244, 249))
            self.setStyleSheet(f"#LoginWindow{{background: {color.name()}}}")

        self.chat_card = ChatListCard(self)
        self.chat_content_card = ChatContentCard(self)

        splitter = QtWidgets.QSplitter(QtGui.Qt.Horizontal)
        splitter.addWidget(self.chat_card)
        splitter.addWidget(self.chat_content_card)
        splitter.setSizes([200, 700])

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 46, 6, 6)
        layout.addWidget(splitter)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    cw = ChatWindow()
    cw.show()

    app.exec_()
