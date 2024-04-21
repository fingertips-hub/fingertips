import os
import locale

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

import win32com.client


class SoftwareItem(QtWidgets.QWidget):
    def __init__(self, icon, name, parent=None):
        super().__init__(parent=parent)
        self._init_ui(icon, name)

    def _init_ui(self, icon, name):
        self.setMaximumSize(100, 100)
        self.setObjectName('software_item')

        self.name_label = QtWidgets.QLabel(name)
        self.img_label = QtWidgets.QLabel()
        self.img_label.setFixedSize(48, 48)

        pixmap = icon.pixmap(48, 48).scaled(
            48, 48, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.img_label.setPixmap(pixmap)

        self.img_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setAlignment(QtCore.Qt.AlignVCenter)
        layout.addWidget(self.img_label)
        layout.addWidget(self.name_label)


class SoftwareListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('software_list_widget')
        self.setFlow(QtWidgets.QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.setSpacing(0)

        self.setAcceptDrops(True)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            files = [u.toLocalFile() for u in event.mimeData().urls()]
            for file in files:
                if file.endswith('.lnk'):
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(file)
                    file = shortcut.Targetpath

                icon = QtWidgets.QFileIconProvider().icon(
                    QtCore.QFileInfo(file))

                custom_widget = SoftwareItem(
                    icon,
                    os.path.basename(file).rsplit('.', 1)[0])

                item = QtWidgets.QListWidgetItem(self)
                item.setSizeHint(QtCore.QSize(100, 100))
                self.setItemWidget(item, custom_widget)
                self.addItem(item)

        else:
            event.setDropAction(QtCore.Qt.MoveAction)
            super().dropEvent(event)

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
