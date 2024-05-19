import sys
import ctypes

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
import qtawesome
import qfluentwidgets

from fingertips.utils import get_logger
from fingertips.window import Fingertips
from fingertips.settings.main import SettingsWindow


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
    window = Fingertips()

    menu = QtWidgets.QMenu()
    tray.setContextMenu(menu)

    settings_window = SettingsWindow()

    add_action(menu, '主窗口', lambda: window.set_visible(), app, 'ri.window-line')
    add_action(menu, '系统配置', settings_window.show, app, 'fa.gear')
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
    app.setAttribute(QtCore.Qt.AA_DontCreateNativeWidgetSiblings)

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('fingertips')

    qfluentwidgets.setThemeColor('#AB62BA')
    tray = create_tray(app)
    tray.show()

    sys.exit(app.exec_())
