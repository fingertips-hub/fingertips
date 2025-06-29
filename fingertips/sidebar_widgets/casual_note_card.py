from PySide2 import QtWidgets, QtCore, QtGui

import qfluentwidgets
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget


class TextDialog(QtWidgets.QDialog):
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setWindowTitle("随手记事")
        self.setFixedSize(600, 800)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        self.text_edit = qfluentwidgets.TextEdit(self)
        self.text_edit.setPlainText(text)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.text_edit)


class CasualNoteCard(SidebarWidget):
    name = '随手记事'
    category = '生活'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('随手记事')
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)

        self.note_text_edit = QtWidgets.QTextEdit(self)
        self.note_text_edit.setPlaceholderText('输入您的笔记...')
        self.note_text_edit.mouseDoubleClickEvent = self.note_double_clicked
        self.note_text_edit.focusOutEvent = self.note_double_focus_out

        self.note_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border:  none;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                color: #333;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.note_text_edit)
        self.setLayout(layout)

    def note_double_clicked(self, event):
        dialog = TextDialog(self.note_text_edit.toPlainText())
        dialog.exec_()

        self.note_text_edit.setPlainText(dialog.text_edit.toPlainText())

        super(QtWidgets.QTextEdit, self.note_text_edit).mouseDoubleClickEvent(event)

    def note_double_focus_out(self, event):
        self.save_config_signal.emit()
        super(QtWidgets.QTextEdit, self.note_text_edit).focusOutEvent(event)

    def get_config(self):
        return {'note': self.note_text_edit.toPlainText()}

    def set_config(self, config):
        self.note_text_edit.setPlainText(config.get('note', ''))


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = CasualNoteCard()
    widget.show()
    app.exec_()
