from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore

import qfluentwidgets
from qfluentwidgets import FluentIcon


class LineEditSettingCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, text='', is_password=False,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent)

        if is_password:
            self.line_edit = qfluentwidgets.PasswordLineEdit(self)
        else:
            self.line_edit = qfluentwidgets.LineEdit(self)
        self.line_edit.setMinimumWidth(300)
        self.line_edit.setText(text)
        self.hBoxLayout.addWidget(self.line_edit)
        self.hBoxLayout.addSpacing(16)


class SpinBoxSettingCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, value=0.0, content=None, parent=None):
        super().__init__(icon, title, content, parent)

        self.spin_box = qfluentwidgets.DoubleSpinBox(self)
        self.spin_box.setValue(value)
        self.hBoxLayout.addWidget(self.spin_box)
        self.hBoxLayout.addSpacing(16)


class SettingPage(qfluentwidgets.ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget()

    def _init_widget(self):
        self.setObjectName('setting_page')

        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidgetResizable(True)

        self.scroll_widget = QtWidgets.QWidget()
        self.expand_layout = qfluentwidgets.ExpandLayout(self.scroll_widget)
        self.setWidget(self.scroll_widget)

        self.ai_group = qfluentwidgets.SettingCardGroup(
            '全局AI设置', self.scroll_widget)

        self.openai_base_card = LineEditSettingCard(
            FluentIcon.VPN,
            'OpenAI 代理地址',
            'https://oneapi.gptnb.me/v1',
            content='除默认地址外，必须包含 http(s)://',
            parent=self.ai_group
        )
        self.openai_key_card = LineEditSettingCard(
            FluentIcon.VPN,
            'OpenAI API Key',
            is_password=True,
            content='使用自己的 OpenAI Key',
            parent=self.ai_group
        )
        self.default_model_card = LineEditSettingCard(
            FluentIcon.VPN,
            '默认模型',
            'gpt-3.5-turbo',
            content='全局默认使用的模型',
            parent=self.ai_group
        )
        self.default_temperature_card = SpinBoxSettingCard(
            FluentIcon.VPN,
            '默认 Temperature',
            0.6,
            '设置默认 Temperature 值',
            self.ai_group
        )

        self.ai_group.addSettingCard(self.openai_base_card)
        self.ai_group.addSettingCard(self.openai_key_card)
        self.ai_group.addSettingCard(self.default_model_card)
        self.ai_group.addSettingCard(self.default_temperature_card)

        self.expand_layout.setSpacing(28)
        self.expand_layout.setContentsMargins(20, 10, 20, 0)
        self.expand_layout.addWidget(self.ai_group)

        self.setStyleSheet('*{outline: none}')


# class SettingPageWidget(QtWidgets.QFrame):
#
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         self.setObjectName('setting_page')
#         self.h_box_layout = QtWidgets.QHBoxLayout(self)
#         self.setting_page = SettingPage(self)
#         self.h_box_layout.addWidget(self.setting_page)
