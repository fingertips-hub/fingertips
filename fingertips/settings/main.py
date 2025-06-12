import sys

from PySide2 import QtGui

from PySide2.QtCore import Qt, QUrl
from PySide2.QtGui import QDesktopServices, QGuiApplication
from PySide2.QtWidgets import QApplication, QFrame, QHBoxLayout

from qfluentwidgets import (NavigationItemPosition, MessageBox, MSFluentWindow,
                            SubtitleLabel, setFont)
from qfluentwidgets import FluentIcon as FIF

from fingertips.settings.setting_page import SettingPage
from fingertips.settings.ai_action_page import AIActionPage
from fingertips.settings.super_sidebar_page import SuperSideBarPage


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class SettingsWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon('res/icon.png'))
        self.setWindowTitle('配置中心')

        # create sub interface
        self.setting_page = SettingPage(self)
        self.ai_action_page = AIActionPage(self)
        self.videoInterface = Widget('Video Interface', self)
        self.sidebar_page = SuperSideBarPage(self)
        # self.libraryInterface = Widget('library Interface', self)

        self.initNavigation()

    def initNavigation(self):
        self.addSubInterface(self.setting_page, FIF.SETTING, '设置',
                             FIF.SETTING)
        self.addSubInterface(self.ai_action_page, FIF.APPLICATION, 'AI功能')
        self.addSubInterface(self.videoInterface, FIF.DEVELOPER_TOOLS, '工具')
        self.addSubInterface(self.sidebar_page, FIF.ALIGNMENT, '超级侧栏')
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.setting_page.objectName())

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://afdian.net/a/zhiyiYo"))

    def show(self):
        self.resize(900, 700)
        desktop = QGuiApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        super().show()


if __name__ == '__main__':
    app = QApplication([])
    sw = SettingsWindow()
    sw.show()
    app.exec_()