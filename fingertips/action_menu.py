from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import qfluentwidgets
from qfluentwidgets import FluentIcon as FIF


class ActionMenu(qfluentwidgets.RoundMenu):
    def __init__(self, title='', parent=None):
        super().__init__(title, parent)

        # add actions
        self.addAction(qfluentwidgets.Action(FIF.COPY, 'Copy'))
        self.addAction(qfluentwidgets.Action(FIF.CUT, 'Cut'))
        self.actions()[0].setCheckable(True)
        self.actions()[0].setChecked(True)

        # add sub menu
        submenu = qfluentwidgets.RoundMenu("Add to", self)
        submenu.setIcon(FIF.ADD)
        submenu.addActions([
            qfluentwidgets.Action(FIF.VIDEO, 'Video'),
            qfluentwidgets.Action(FIF.MUSIC, 'Music'),
        ])
        self.addMenu(submenu)

        # add actions
        self.addActions([
            qfluentwidgets.Action(FIF.PASTE, 'Paste'),
            qfluentwidgets.Action(FIF.CANCEL, 'Undo')
        ])

        # add separator
        self.addSeparator()
        self.addAction(QtWidgets.QAction(f'Select all', shortcut='Ctrl+A'))

        # insert actions
        self.insertAction(
            self.actions()[-1],
            qfluentwidgets.Action(FIF.SETTING, 'Settings', shortcut='Ctrl+S'))
        self.insertActions(
            self.actions()[-1],
            [qfluentwidgets.Action(FIF.HELP, 'Help', shortcut='Ctrl+H'),
             qfluentwidgets.Action(FIF.FEEDBACK, 'Feedback',
                                   shortcut='Ctrl+F')]
        )
        self.actions()[-2].setCheckable(True)
        self.actions()[-2].setChecked(True)

    def show_menu(self):
        self.exec(
            QtGui.QCursor().pos(),
            aniType=qfluentwidgets.MenuAnimationType.DROP_DOWN
        )


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    rm = ActionMenu()
    rm.show_menu()

    app.exec_()
