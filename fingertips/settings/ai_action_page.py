from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

import qfluentwidgets
from qfluentwidgets import FluentIcon


class AIActionCard(qfluentwidgets.CardWidget):
    def __init__(self, title, content, enabled, parent=None):
        super().__init__(parent)

        self.title_label = qfluentwidgets.BodyLabel(title, self)
        self.content_label = qfluentwidgets.CaptionLabel(content, self)
        self.more_button = qfluentwidgets.TransparentToolButton(FluentIcon.MORE, self)
        self.more_button.setFixedSize(32, 32)
        self.more_button.clicked.connect(self.more_button_clicked)

        self.enable_button = qfluentwidgets.SwitchButton(self)
        self.enable_button.setOnText('启用')
        self.enable_button.setOffText('停用')
        self.enable_button.setChecked(enabled)

        self.info_layout = QtWidgets.QVBoxLayout()
        self.info_layout.setSpacing(0)
        self.info_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.info_layout.addWidget(self.title_label)
        self.info_layout.addWidget(self.content_label)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(26)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addLayout(self.info_layout)
        layout.addSpacerItem(QtWidgets.QSpacerItem(
            10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        ))
        layout.addWidget(self.enable_button, 0, QtCore.Qt.AlignRight)
        layout.addWidget(self.more_button, 0, QtCore.Qt.AlignRight)

    def more_button_clicked(self):
        menu = qfluentwidgets.RoundMenu(parent=self)
        menu.addAction(qfluentwidgets.Action(FluentIcon.EDIT, '编辑', self))
        menu.addAction(qfluentwidgets.Action(FluentIcon.DELETE, '删除', self))

        x = (self.more_button.width() - menu.width()) // 2 + 10
        pos = self.more_button.mapToGlobal(QtCore.QPoint(x, self.more_button.height()))
        menu.exec(pos)


class AIActions(qfluentwidgets.ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget()

    def _init_widget(self):
        self.setWidgetResizable(True)
        self.scroll_widget = QtWidgets.QWidget()
        self.setWidget(self.scroll_widget)

        self._layout = QtWidgets.QVBoxLayout(self.scroll_widget)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self.setStyleSheet(
            'QScrollArea {border: none; background:transparent}'
        )

    def add_action(self, title, content, enabled=True):
        self._layout.addWidget(AIActionCard(title, content, enabled, self))


class AIActionPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ai_action_page')

        self.add_button = qfluentwidgets.PrimaryPushButton('添加', self)
        self.add_button.setObjectName('add_button')
        self.ai_actions = AIActions(self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(10, 16, 12, 16)
        layout.addWidget(self.add_button, 0, QtCore.Qt.AlignRight)
        layout.addWidget(self.ai_actions)

        self.ai_actions.add_action('Microsoft 使用技巧', 'Microsoft Corporation')
        self.ai_actions.add_action('MSN 天气', 'Microsoft Corporation')

        self.setStyleSheet('#add_button {margin-right: 20px}')