import os

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtWebEngineWidgets

from fingertips.widgets import SoftwareListWidget, InputLineEdit
from fingertips.hotkey import HotkeyThread
from fingertips.settings import GLOBAL_HOTKEYS
from fingertips.core import AskAIThread


class Fingertips(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.placeholder = 'Hello, Fingertips!'

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

        self.input_line_edit = InputLineEdit()
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
        self.software_list_widget.item_double_clicked.connect(
            self.software_list_widget_item_double_clicked)

        self.ask_viewer = QtWebEngineWidgets.QWebEngineView()
        self.ask_viewer.setObjectName('ask_viewer')
        self.ask_viewer.setHtml('<body style="color:white;background-color:#303133;font-size: 14px;padding: 6px;box-sizing: border-box;"></body>')
        # self.ask_viewer.setOpenExternalLinks(True)
        # self.ask_viewer.setReadOnly(True)
        self._set_ask_viewer_status(False)
        # self.ask_viewer.textChanged.connect(self._ask_viewer_scroll_to_bottom)

        inner_layout.addWidget(self.input_line_edit)
        inner_layout.addWidget(self.software_list_widget)
        inner_layout.addWidget(self.ask_viewer)

        # layout.addWidget(self.result_list_widget)

        layout.addWidget(inner_widget)

        self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)

    def _ask_viewer_scroll_to_bottom(self):
        scrollbar = self.ask_viewer.verticalScrollBar()
        # 检查是否已经滚动到底部
        if scrollbar.value() != scrollbar.maximum():
            QtCore.QTimer.singleShot(
                100,
                lambda: scrollbar.setValue(scrollbar.maximum())
            )

    def init_hotkey(self):
        global_shortcuts = GLOBAL_HOTKEYS
        hotkeys = HotkeyThread(global_shortcuts, self)
        hotkeys.show_main_sign.connect(self.set_visible)
        hotkeys.shortcut_triggered.connect(self.shortcut_triggered)
        hotkeys.start()

    def software_list_widget_item_double_clicked(self, exe_path):
        os.startfile(exe_path)
        self.set_visible()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.set_visible()

        return super().keyPressEvent(event)

    def shortcut_triggered(self):
        print('shortcut_triggered')

    def load_style(self):
        with open('res/theme.css') as f:
            self.setStyleSheet(f.read())

    def _set_result(self, text):
        print(text)
        self.ask_viewer.setHtml(text)

    def input_line_edit_return_pressed(self):
        text = self.input_line_edit.text().strip()
        if not text:
            return

        self._set_software_list_widget_status(False)
        self._set_ask_viewer_status(True)

        self._set_result('<body style="color:white;background-color:#303133;font-size: 14px;padding: 6px;box-sizing: border-box;">思考中，请稍后...</body>')
        ask_ai_thread = AskAIThread(text, self)
        ask_ai_thread.resulted.connect(self._set_result)
        ask_ai_thread.start()

    def _set_ask_viewer_status(self, is_show=False):
        if is_show:
            # self.ask_viewer.clear()
            self.ask_viewer.show()
            self.ask_viewer.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred,
                QtWidgets.QSizePolicy.Preferred
            )
            self.ask_viewer.setFixedSize(820, 300)
            self.ask_viewer.adjustSize()
        else:
            self.ask_viewer.hide()
            # self.ask_viewer.clear()
            self.ask_viewer.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored,
                QtWidgets.QSizePolicy.Ignored
            )

    def _set_software_list_widget_status(self, is_show=False):
        if is_show:
            self.software_list_widget.show()
            self.software_list_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred,
                QtWidgets.QSizePolicy.Preferred
            )
            self.software_list_widget.setFixedSize(820, 300)
            self.software_list_widget.adjustSize()
        else:
            self.software_list_widget.hide()
            self.software_list_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored,
                QtWidgets.QSizePolicy.Ignored
            )

    def input_line_edit_text_changed(self, text):
        if text:
            return

        self._set_ask_viewer_status(False)
        self._set_software_list_widget_status(True)

    def set_show(self):
        self.setVisible(True)
        self.activateWindow()
        self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)

    def set_visible(self):
        if self.isVisible():
            self.input_line_edit.setText('')
            self.software_list_widget.clearSelection()
            self.setVisible(False)
        else:
            self.set_show()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    f = Fingertips()
    f.show()
    app.exec_()
