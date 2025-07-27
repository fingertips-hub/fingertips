import os
import sys
import ctypes
from functools import partial

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
import qtawesome
import qfluentwidgets

from fingertips.utils import get_logger
from fingertips.window import Fingertips
from fingertips.settings.main import SettingsWindow
from fingertips.chat.main import ChatWindow
from fingertips.super_sidebar import SuperSidebar
from fingertips.settings.config_model import config_model
from fingertips.widget_utils import signal_bus


log = get_logger('tray')


def add_action(menu, name, connect_func, parent, icon=None):
    if icon:
        if not isinstance(icon, QtGui.QIcon):
            icon = qtawesome.icon(icon)
        action = qfluentwidgets.Action(icon, name, parent)
    else:
        action = qfluentwidgets.Action(name, parent)
    action.triggered.connect(connect_func)
    menu.addAction(action)
    return action


def init_super_sidebar(tray, value=None):
    if tray.super_sidebar:
        tray.super_sidebar.hide_panel()
        tray.super_sidebar.deleteLater()
        tray.super_sidebar = None

    if config_model.enable_super_sidebar.value:
        tray.super_sidebar = SuperSidebar(
            config_model.super_sidebar_position.value,
            config_model.super_sidebar_width.value,
            config_model.super_sidebar_opacity.value,
            config_model.super_sidebar_type.value == 'acrylic',
        )


def cleanup_and_exit(app, tray, window, chat_window, settings_window):
    """正确清理所有资源并退出应用程序"""
    log.info('开始清理应用程序资源...')
    
    try:
        # 1. 优先停止热键线程 - 这是最关键的
        if window and hasattr(window, 'hotkeys'):
            log.info('优先停止热键线程...')
            try:
                if window.hotkeys.isRunning():
                    window.hotkeys.stop()
                    # 短暂等待，如果不成功就强制终止
                    if not window.hotkeys.wait(500):
                        log.warning('热键线程未能正常停止，强制终止')
                        window.hotkeys.terminate()
                        window.hotkeys.wait(500)
            except Exception as e:
                log.warning(f'停止热键线程时出错: {e}')
        
        # 2. 简单停止一些定时器
        log.info('停止主要定时器...')
        try:
            all_widgets = QtWidgets.QApplication.allWidgets()
            for obj in all_widgets:
                if hasattr(obj, 'children'):
                    for child in obj.children():
                        if isinstance(child, QtCore.QTimer):
                            try:
                                child.stop()
                            except Exception:
                                pass
        except Exception as e:
            log.warning(f'停止定时器时出错: {e}')
        
        # 3. 清理SuperSidebar
        if hasattr(tray, 'super_sidebar') and tray.super_sidebar:
            log.info('清理SuperSidebar...')
            try:
                tray.super_sidebar.hide_panel()
                tray.super_sidebar.close()
                tray.super_sidebar = None
            except Exception as e:
                log.warning(f'清理SuperSidebar时出错: {e}')
        
        # 4. 断开托盘菜单连接
        if tray:
            log.info('清理托盘菜单...')
            try:
                # 断开action信号连接
                if hasattr(tray, 'main_action'):
                    tray.main_action.triggered.disconnect()
                if hasattr(tray, 'chat_action'):
                    tray.chat_action.triggered.disconnect()
                if hasattr(tray, 'settings_action'):
                    tray.settings_action.triggered.disconnect()
                if hasattr(tray, 'exit_action'):
                    tray.exit_action.triggered.disconnect()
                
                # 清除菜单
                tray.setContextMenu(None)
                tray.hide()
            except Exception as e:
                log.warning(f'清理托盘时出错: {e}')
        
        # 5. 关闭主要窗口
        try:
            if window:
                window.close()
            if chat_window:
                chat_window.close()
            if settings_window:
                settings_window.close()
        except Exception as e:
            log.warning(f'关闭窗口时出错: {e}')
        
        # 6. 简单的事件处理
        log.info('处理剩余事件...')
        try:
            for _ in range(3):
                app.processEvents()
                QtCore.QThread.msleep(50)
        except Exception:
            pass
        
        log.info('资源清理完成，退出应用程序')
        
    except Exception as e:
        log.error(f'清理资源时出错: {e}')
    
    finally:
        try:
            log.info('退出应用程序')
            app.quit()
        except Exception:
            # 最后手段：强制退出
            import os
            log.warning('强制退出')
            os._exit(0)


def create_tray(app):
    tray = QtWidgets.QSystemTrayIcon()
    tray.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'res/icon.png')))

    chat_window = ChatWindow()
    window = Fingertips(chat_window)

    menu = qfluentwidgets.SystemTrayMenu()
    tray.setContextMenu(menu)

    settings_window = SettingsWindow()

    # 使用普通函数替代lambda，避免回调警告
    def show_main_window():
        window.set_visible()
    
    def exit_application():
        cleanup_and_exit(app, tray, window, chat_window, settings_window)

    # 保存action引用以便后续清理
    tray.main_action = add_action(menu, '主窗口', show_main_window, app, 'ri.window-line')
    tray.chat_action = add_action(menu, '聊天窗口', chat_window.show, app, qfluentwidgets.FluentIcon.CHAT.icon())
    tray.settings_action = add_action(menu, '系统配置', settings_window.show, app, 'fa6s.gear')
    tray.exit_action = add_action(menu, '退出', exit_application, app, 'mdi.power-standby')

    tray.super_sidebar = None
    init_super_sidebar(tray)
    
    # 保存信号连接以便后续断开
    tray.sidebar_connection = signal_bus.super_sidebar_config_changed.connect(partial(init_super_sidebar, tray))

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
    # qfluentwidgets.setThemeColor('#6651F0')
    tray = create_tray(app)
    tray.show()

    sys.exit(app.exec_())
