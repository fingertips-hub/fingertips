from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

import win32api
import win32con
import win32gui

from fingertips.widgets import SoftwareListWidget
from fingertips.hotkey import HotkeyThread
from fingertips.settings import GLOBAL_HOTKEYS


class LineEdit(QtWidgets.QLineEdit):
    def mousePressEvent(self, event):
        self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
        win32gui.ReleaseCapture()
        win32api.SendMessage(
            int(self.window().winId()),
            win32con.WM_SYSCOMMAND,
            win32con.SC_MOVE | win32con.HTCAPTION,
            0
        )
        self.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        event.ignore()
        super().mousePressEvent(event)


class Fingertips(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.placeholder = 'Hello, Fingertips!'
        self.clipboard = QtWidgets.QApplication.clipboard()

        pos = QtWidgets.QDesktopWidget().availableGeometry().center()
        pos.setX(pos.x() - (self.width() / 2) - 100)
        pos.setY(pos.y() - (pos.y() / 2))
        self.move(pos)

        self.init_ui()
        self.init_hotkey()

    def init_ui(self):
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        self.setFixedSize(QtCore.QSize(830, 380))

        self.load_style()
        self.installEventFilter(self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        inner_widget = QtWidgets.QWidget()
        inner_widget.setObjectName('inner_widget')
        inner_layout = QtWidgets.QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.setSpacing(6)

        self.input_line_edit = LineEdit()
        self.input_line_edit.setPlaceholderText(self.placeholder)
        self.input_line_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.input_line_edit.setMinimumHeight(66)
        self.input_line_edit.returnPressed.connect(
            self.input_line_edit_return_pressed)
        self.input_line_edit.textChanged.connect(
            self.input_line_edit_text_changed)

        # self.result_list_widget = QtWidgets.QListWidget()
        # self.result_list_widget.setObjectName('result_list_widget')
        # self.result_list_widget.setFocusPolicy(Qt.ClickFocus)
        # self.result_list_widget.keyPressEvent = self.result_list_key_press_event
        # self.result_list_widget.itemClicked.connect(self.execute_result_item)
        #

        self.software_list_widget = SoftwareListWidget()
        self.software_list_widget.setObjectName('software_list_widget')

        inner_layout.addWidget(self.input_line_edit)
        inner_layout.addWidget(self.software_list_widget)
        # layout.addWidget(self.result_list_widget)

        layout.addWidget(inner_widget)

        self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)

    def init_hotkey(self):
        global_shortcuts = GLOBAL_HOTKEYS
        hotkeys = HotkeyThread(global_shortcuts, self)
        hotkeys.show_main_sign.connect(self.set_visible)
        hotkeys.shortcut_triggered.connect(self.shortcut_triggered)
        hotkeys.start()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.set_visible()

        return super().keyPressEvent(event)

    def shortcut_triggered(self):
        print('shortcut_triggered')

    def load_style(self):
        with open('res/theme.css') as f:
            self.setStyleSheet(f.read())

    def input_line_edit_return_pressed(self, text):
        pass

    def input_line_edit_text_changed(self, text):
        pass

    def set_show(self):
        self.setVisible(True)
        self.activateWindow()
        self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)

    def set_visible(self):
        if self.isVisible():
            self.input_line_edit.setText('')
            self.setVisible(False)
        else:
            self.set_show()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    f = Fingertips()
    f.show()
    app.exec_()
