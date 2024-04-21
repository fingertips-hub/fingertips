import sys
import ctypes

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
import qtawesome

from fingertips.utils import get_logger


log = get_logger('tray')


def add_action(menu, name, connect_func, parent, icon=None):
    if icon:
        icon = qtawesome.icon(icon)
        action = QtWidgets.QAction(icon, name, parent)
    else:
        action = QtWidgets.QAction(name, parent)
    action.triggered.connect(connect_func)
    menu.addAction(action)
    return action


def create_tray(app):
    tray = QtWidgets.QSystemTrayIcon()
    tray.setIcon(QtGui.QIcon('res/icon.png'))

    menu = QtWidgets.QMenu()
    tray.setContextMenu(menu)

    add_action(menu, '主窗口', lambda: print('打开主窗口'), app, 'ri.window-line')
    add_action(menu, '插件商城', lambda: print('打开插件商城'), app,
               'mdi.storefront-outline')
    add_action(menu, '系统配置', lambda: print('打开系统配置'), app, 'fa.gear')
    add_action(menu, '退出', app.exit, app, 'mdi.power-standby')

    return tray


if __name__ == '__main__':
    log.info('===============启动Fingertips==================')

    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QtGui.QIcon('res/icon.png'))

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('fingertips')

    tray = create_tray(app)
    tray.show()

    sys.exit(app.exec_())
