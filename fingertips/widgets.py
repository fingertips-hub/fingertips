import os

from PySide2 import QtWidgets
from PySide2 import QtCore

import win32com.client


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
            for source_file in files:
                if source_file.endswith('.lnk'):
                    shell = win32com.client.Dispatch('WScript.Shell')
                    shortcut = shell.CreateShortCut(source_file)
                    file = shortcut.Targetpath
                else:
                    file = source_file

                icon = QtWidgets.QFileIconProvider().icon(
                    QtCore.QFileInfo(file))

                custom_widget = SoftwareItem(
                    icon,
                    os.path.basename(source_file).rsplit('.', 1)[0])

                item = QtWidgets.QListWidgetItem(self)
                item.setSizeHint(QtCore.QSize(88, 86))
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
