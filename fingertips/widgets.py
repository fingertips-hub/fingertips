import os

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWebEngineWidgets

import win32api
import win32con
import win32gui
import win32com.client
import qtawesome as qta

from fingertips.db_utils import SoftwareDB


class SoftwareItem(QtWidgets.QWidget):
    def __init__(self, icon, name, parent=None):
        super().__init__(parent=parent)
        self._init_ui(icon, name)

    def _init_ui(self, icon, name):
        self.setMaximumSize(88, 86)
        self.setObjectName('software_item')

        self.name_label = QtWidgets.QLabel(name)
        self.img_label = QtWidgets.QLabel()
        self.img_label.setFixedSize(34, 34)

        pixmap = icon.pixmap(34, 34).scaled(
            34, 34, QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.img_label.setPixmap(pixmap)

        img_layout = QtWidgets.QHBoxLayout()
        img_layout.addItem(QtWidgets.QSpacerItem(
            34, 100, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        ))
        img_layout.addWidget(self.img_label)

        img_layout.addItem(QtWidgets.QSpacerItem(
            34, 100, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        ))

        self.img_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.addLayout(img_layout)
        layout.addWidget(self.name_label)


class SoftwareListWidget(QtWidgets.QListWidget):
    item_double_clicked = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._software_db = SoftwareDB()

        self.setObjectName('software_list_widget')
        self.setFlow(QtWidgets.QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.setSpacing(0)

        self.setAcceptDrops(True)
        self.itemDoubleClicked.connect(self._item_double_clicked)

        for info in self._software_db.get_software():
            self.add_item(info['name'], info['exe_path'])

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            files = [
                u.toLocalFile() for u in event.mimeData().urls() if
                u.toLocalFile().endswith(('.lnk', '.exe'))
            ]
            for source_file in files:
                if source_file.endswith('.lnk'):
                    shell = win32com.client.Dispatch('WScript.Shell')
                    shortcut = shell.CreateShortCut(source_file)
                    file = shortcut.Targetpath
                else:
                    file = source_file

                name = os.path.basename(source_file).rsplit('.', 1)[0]
                res = self._software_db.add_software(name, file)
                if res:
                    self.add_item(name, file)

        else:
            event.setDropAction(QtCore.Qt.MoveAction)
            super().dropEvent(event)

    def add_item(self, name, file_path):
        icon = QtWidgets.QFileIconProvider().icon(
            QtCore.QFileInfo(file_path))

        custom_widget = SoftwareItem(icon, name)

        item = QtWidgets.QListWidgetItem(self)
        item.setSizeHint(QtCore.QSize(88, 86))
        item.exe_path = file_path
        self.setItemWidget(item, custom_widget)
        self.addItem(item)

    def _item_double_clicked(self, item):
        self.item_double_clicked.emit(item.exe_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)


class InputLineEdit(QtWidgets.QLineEdit):
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


class AskAIView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.page().setBackgroundColor(QtGui.QColor('#303133'))

    def contextMenuEvent(self, event):
        pass


class AskAIWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.is_loading = False

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignRight)
        header_layout.setContentsMargins(0, 0, 12, 0)

        self.button = QtWidgets.QPushButton()
        self.button.setStyleSheet(
            'background-color: #303133; border: 0px')
        header_layout.addWidget(self.button)
        layout.addLayout(header_layout)

        self.spin_icon = qta.icon(
            'fa5s.spinner', color='#ddd', animation=qta.Spin(self.button)
        )

        self.ask_view = AskAIView()
        layout.addWidget(self.ask_view)

        self.button.clicked.connect(self.button_clicked)

    def button_clicked(self):
        if self.is_loading:
            return

        print('copy...')

    def hide_loading(self):
        self.is_loading = False
        self.button.setIcon(qta.icon('fa.paper-plane', color='#eee'))

    def show_loading(self):
        self.is_loading = True
        self.button.setIcon(self.spin_icon)

    def set_html(self, html):
        self.ask_view.setHtml(html)
