from PySide2 import QtWidgets
from qfluentwidgets import SimpleCardWidget, TabBar, TabCloseButtonDisplayMode


class SoftwareCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tabCount = 1
        self.setObjectName('SoftwareCard')
        self.setFixedHeight(200)

        self.tabBar = TabBar(self)
        self.tabBar.setMovable(True)
        self.tabBar.setScrollable(True)
        self.tabBar.setTabShadowEnabled(True)
        self.tabBar.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ON_HOVER)
        self.tabBar.setTabMaximumWidth(100)

        self.stacked_widget = QtWidgets.QStackedWidget(self)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.view = QtWidgets.QWidget()
        self.view_layout = QtWidgets.QVBoxLayout(self.view)
        self.main_layout.addWidget(self.view, 1)

        self.view_layout.addWidget(self.tabBar)
        self.view_layout.addWidget(self.stacked_widget)
        self.view_layout.setContentsMargins(0, 0, 0, 0)

        self.tabBar.tabAddRequested.connect(self.add_tab)

    def add_tab(self):
        widget = QtWidgets.QLabel('666')
        text = '日常'
        object_name = f'tab{self.tabCount}'
        widget.setObjectName(object_name)
        self.tabBar.addTab(
            object_name,
            text,
            onClick=lambda: self.stacked_widget.setCurrentWidget(widget)
        )
        self.tabCount += 1


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = SoftwareCard()
    w.show()
    app.exec_()
