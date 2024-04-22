from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

from widgets import SoftwareItem, SoftwareListWidget


class Fingertips(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.placeholder = 'Hello, Fingertips!'
        self.clipboard = QtWidgets.QApplication.clipboard()

        pos = QtWidgets.QDesktopWidget().availableGeometry().center()
        pos.setX(pos.x() - (self.width() / 2) - 100)
        pos.setY(pos.y() - (pos.y() / 2) - 380)
        self.move(pos)

        self.init_ui()

    def init_ui(self):
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        self.setFixedSize(QtCore.QSize(830, 710))

        self.load_style()
        self.installEventFilter(self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        inner_widget = QtWidgets.QWidget()
        inner_widget.setObjectName('inner_widget')
        inner_layout = QtWidgets.QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.setSpacing(6)

        self.input_line_edit = QtWidgets.QLineEdit()
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
        layout.addItem(QtWidgets.QSpacerItem(
            40, 100, QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        ))

        layout.addWidget(inner_widget)

        self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)

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


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    f = Fingertips()
    f.show()
    app.exec_()
