from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import qfluentwidgets
from qfluentwidgets import FluentIcon as FIF

from fingertips.db_utils import AIActionDB


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
