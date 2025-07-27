import os

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWebEngineWidgets

import win32api
import win32con
import win32gui
import qtawesome as qta

from fingertips.db_utils import SoftwareDB
from fingertips.utils import get_exe_path


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
            self.add_item(info['name'], info['exe_path'], info['lnk_path'])

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            files = [
                u.toLocalFile() for u in event.mimeData().urls() if
                u.toLocalFile().endswith(('.lnk', '.exe')) or
                os.path.isdir(u.toLocalFile())
            ]
            for source_file in files:
                file = get_exe_path(source_file)
                name = os.path.basename(source_file).rsplit('.', 1)[0]
                res = self._software_db.add_software(name, file, source_file)
                if res:
                    self.add_item(name, file, source_file)

        else:
            event.setDropAction(QtCore.Qt.MoveAction)
            super().dropEvent(event)

    def add_item(self, name, file_path, lnk_path):
        icon = QtWidgets.QFileIconProvider().icon(
            QtCore.QFileInfo(file_path))

        custom_widget = SoftwareItem(icon, name)

        item = QtWidgets.QListWidgetItem(self)
        item.setSizeHint(QtCore.QSize(88, 86))
        item.path = lnk_path or file_path
        self.setItemWidget(item, custom_widget)
        self.addItem(item)

    def _item_double_clicked(self, item):
        self.item_double_clicked.emit(item.path)

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
        self.source_text = ''

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignRight)
        header_layout.setContentsMargins(0, 0, 12, 0)

        self.button = QtWidgets.QPushButton()
        self.copy_button = QtWidgets.QPushButton()
        self.button.setIconSize(QtCore.QSize(20, 20))
        self.copy_button.setIconSize(QtCore.QSize(26, 26))

        button_style = 'background-color: #303133; border: 0px'
        self.button.setStyleSheet(button_style)
        self.copy_button.setStyleSheet(button_style)

        header_layout.addWidget(self.button)
        header_layout.addWidget(self.copy_button)
        layout.addLayout(header_layout)

        self.spin_icon = qta.icon(
            'fa5s.spinner', color='#ddd', animation=qta.Spin(self.button)
        )
        self.publish_icon = qta.icon('fa5s.paper-plane', color='#eee')

        self.enable_copy_icon = qta.icon('ri.file-copy-2-fill', color='#ddd')
        self.disable_copy_icon = qta.icon('ri.file-copy-2-fill', color='#555')

        self.ask_view = AskAIView()
        layout.addWidget(self.ask_view)

        self.button.clicked.connect(self.button_clicked)
        self.copy_button.clicked.connect(self.copy_button_clicked)

    def button_clicked(self):
        if self.is_loading:
            return

        print('submit...')

    def copy_button_clicked(self):
        QtWidgets.QApplication.clipboard().setText(self.source_text)
        print('copy finished...')

    def hide_loading(self):
        self.is_loading = False
        self.copy_button.setIcon(self.enable_copy_icon)
        self.copy_button.setEnabled(True)
        self.button.setIcon(self.publish_icon)

    def show_loading(self):
        self.is_loading = True
        self.copy_button.setIcon(self.disable_copy_icon)
        self.copy_button.setEnabled(False)
        self.button.setIcon(self.spin_icon)

    def set_html(self, html):
        self.ask_view.setHtml(html)


class ResultItem(QtWidgets.QWidget):
    def __init__(self, title, description, keyword='', icon='', date_time='',
                 checkbox=None, parent=None):
        super(ResultItem, self).__init__(parent)

        self.title = title
        self.description = description
        self.keyword = keyword
        self.icon = icon
        self.date_time = date_time  # int list,eg:[2021, 1, 21, 15, 21, 11]
        self.checkbox = checkbox

        self.init_ui()

    def init_ui(self):
        self.setObjectName('result_item')
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 5, 5, 5)
        self.main_layout.setSpacing(12)

        self.img_label = QtWidgets.QLabel()
        self.img_label.setObjectName('img_label')
        self.img_label.setFixedSize(60, 60)
        if self.icon:
            pix_map = QtGui.QPixmap(self.icon).scaled(
                50, 50, QtCore.Qt.IgnoreAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            self.img_label.setPixmap(pix_map)
        else:
            self.img_label.setText(self.keyword)

        self.body_layout = QtWidgets.QVBoxLayout()
        self.body_layout.setSpacing(0)

        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel()
        self.title_label.setObjectName('title_label')
        if self.keyword:
            self.title_label.setText(
                u'{} ({})'.format(self.title, self.keyword))
        else:
            self.title_label.setText(self.title)
        self.title_layout.addWidget(self.title_label)
        if self.date_time:
            self.date_time_edit = QtWidgets.QDateTimeEdit()
            self.date_time_edit.setDateTime(QtCore.QDateTime(*self.date_time))
            self.title_layout.addWidget(self.date_time_edit)
        self.title_layout.addItem(
            QtWidgets.QSpacerItem(120, 30,
                                  QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Minimum)
        )

        self.description_label = QtWidgets.QLabel()
        self.description_label.setObjectName('description_label')
        self.description_label.setText(self.description)

        self.body_layout.addLayout(self.title_layout)
        self.body_layout.addWidget(self.description_label)

        self.main_layout.addWidget(self.img_label)
        self.main_layout.addLayout(self.body_layout)
        if self.checkbox is not None:
            self.todo_checkbox = QtWidgets.QCheckBox()
            self.todo_checkbox.setChecked(self.checkbox)
            self.main_layout.addWidget(self.todo_checkbox)

        self.load_style()

    def load_style(self):
        with open(os.path.join(os.path.dirname(__file__), 'res/result_item.css')) as f:
            self.setStyleSheet(f.read())


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)

    ri = ResultItem(u'百度搜索', u'快速进行百度搜索', 'ctrl+1',
                    'plugins/a.jpg')
    ri.show()

    sys.exit(app.exec_())
