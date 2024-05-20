from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
import qtawesome as qta

import qframelesswindow
import qfluentwidgets
from qfluentwidgets import FluentIcon as FIF

from fingertips.db_utils import AIActionDB
from fingertips.core.thread import AskAIThread
from fingertips.utils import get_select_entity


class AIResultWindow(qframelesswindow.FramelessDialog):
    closed = QtCore.Signal()

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.is_loading = False
        self.data = data
        self.ask_res_thread = None

        self.resize(600, 400)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.setTitleBar(qframelesswindow.StandardTitleBar(self))
        self.titleBar.setIcon(QtGui.QIcon('res/icon.png'))
        self.titleBar.setTitle(data['action']['name'])
        self.titleBar.minBtn.hide()
        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)
        self.windowEffect.disableMaximizeButton(self.winId())
        self.titleBar.raise_()

        self.resend_button = QtWidgets.QToolButton(self)
        self.resend_button.setMinimumSize(38, 34)
        self.resend_button.clicked.connect(self.resend_button_clicked)

        self.spin_icon = qta.icon(
            'fa5s.spinner', color='#AB62BA', animation=qta.Spin(self.resend_button)
        )

        self.super_switch = qfluentwidgets.SwitchButton(self)
        self.super_switch.setOnText('')
        self.super_switch.setOffText('')
        self.super_switch.setToolTip(
            '当启用该项时，可以划词后直接点击重试按钮进行请求，无需再通过菜单调用插件')
        self.super_switch.installEventFilter(qfluentwidgets.ToolTipFilter(self.super_switch, 0))

        self.copy_button = qfluentwidgets.ToolButton(FIF.COPY, self)
        self.copy_button.clicked.connect(self.copy_button_clicked)

        self.view = qfluentwidgets.TextEdit()
        self.view.setReadOnly(True)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(qfluentwidgets.BodyLabel('便捷模式:', self))
        header_layout.addWidget(self.super_switch)
        header_layout.addSpacerItem(QtWidgets.QSpacerItem(
            10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        ))
        header_layout.addWidget(self.resend_button, 0, QtCore.Qt.AlignRight)
        header_layout.addWidget(self.copy_button, 0, QtCore.Qt.AlignRight)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 40, 12, 12)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addLayout(header_layout)
        layout.addWidget(self.view)

        qfluentwidgets.FluentStyleSheet.DIALOG.apply(self)

    def copy_button_clicked(self):
        QtWidgets.QApplication.clipboard().setText(self.view.toPlainText().strip())

    def resend_button_clicked(self):
        if self.is_loading:
            self.ask_res_thread.requestInterruption()
            return

        if self.super_switch.isChecked():
            data = get_select_entity()
            if data['type'] == 'text':
                self.data['select'].update(data)
            elif data['type'] == 'empty':
                pass
            else:
                return qfluentwidgets.InfoBar.error('', '请选择先文字类型的内容', parent=self)

        self.request()

    def set_view(self, text):
        self.view.setMarkdown(text)

    def show_loading(self):
        self.is_loading = True
        self.resend_button.setIcon(self.spin_icon)

    def hide_loading(self):
        self.is_loading = False
        self.resend_button.setIcon(FIF.SYNC.icon())
        self.resend_button.update()

    def request(self):
        self.view.setText('')

        self.ask_res_thread = AskAIThread(
            self.data['select']['text'],
            self.data['action']['model'],
            self.data['action']['temperature'],
            self.data['action']['max_tokens'],
            self.data['action']['prompt'],
            convert_markdown=False,
            parent=self
        )

        self.ask_res_thread.resulted.connect(self.set_view)
        self.ask_res_thread.finished.connect(self.hide_loading)
        self.ask_res_thread.start()

        self.show_loading()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class ActionMenu(qfluentwidgets.RoundMenu):
    triggered = QtCore.Signal(dict)

    def __init__(self, title='', parent=None):
        super().__init__(title, parent)
        self.db = AIActionDB()
        self.data = None

        # add sub menu
        submenu = qfluentwidgets.RoundMenu('AI', self)
        submenu.setIcon(FIF.ROBOT)

        actions = []
        for data in self.db.get_actions():
            if not data['enabled']:
                continue
            action = qfluentwidgets.Action(data['name'])
            action.setToolTip(data['description'])
            action.triggered.connect(partial(self.action_triggered, data))
            actions.append(action)

        submenu.addActions(actions)
        self.addMenu(submenu)

    def action_triggered(self, action_data):
        self.triggered.emit({
            'select': self.data,
            'action': action_data
        })

    def show_menu(self, data):
        self.data = data
        self.exec(
            QtGui.QCursor().pos(),
            aniType=qfluentwidgets.MenuAnimationType.DROP_DOWN
        )


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    rm = ActionMenu()
    rm.show_menu()

    app.exec_()
