from PySide2 import QtWidgets
from PySide2 import QtCore

import qfluentwidgets
from qfluentwidgets import FluentIcon

from fingertips.common_widgets import LineEditSettingCard as _LineEditSettingCard
from fingertips.common_widgets import DoubleSpinBoxSettingCard as _DoubleSpinBoxSettingCard
from fingertips.settings.config_model import config_model


class LineEditSettingCard(_LineEditSettingCard):
    def line_edit_finished(self):
        # todo 实现保存
        pass


class DoubleSpinBoxSettingCard(_DoubleSpinBoxSettingCard):
    def spin_box_value_changed(self, value):
        pass


class SpinBoxSettingCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, config_item, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_item = config_item

        self.spin_box = qfluentwidgets.SpinBox(self)
        self.spin_box.setValue(config_item.value)
        self.hBoxLayout.addWidget(self.spin_box)
        self.hBoxLayout.addSpacing(16)

        self.spin_box.valueChanged.connect(self.spin_box_value_changed)

    def spin_box_value_changed(self, value):
        pass


class TextCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, config_item, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_item = config_item

        self.text_edit = qfluentwidgets.TextEdit()
        self.text_edit.setPlainText(self.config_item.value)
        self.text_edit.setMinimumWidth(300)
        self.hBoxLayout.addWidget(self.text_edit)
        self.hBoxLayout.setContentsMargins(16, 6, 0, 6)
        self.hBoxLayout.addSpacing(16)


class ConfigItemProxy(object):
    @property
    def value(self):
        return ''

    @property
    def range(self):
        return 0, 2


class FloatConfigItemProxy(object):
    @property
    def value(self):
        return 1

    @property
    def range(self):
        return 0, 2


class ChatSettingScrollArea(qfluentwidgets.ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(10, 10, 10, 10)
        self.setWidgetResizable(True)

        self.scroll_widget = QtWidgets.QWidget()
        self.expand_layout = qfluentwidgets.ExpandLayout(self.scroll_widget)
        self.setWidget(self.scroll_widget)

        self.group = qfluentwidgets.SettingCardGroup('设置', self.scroll_widget)

        self.name_card = LineEditSettingCard(
            FluentIcon.TAG,
            '标题',
            ConfigItemProxy(),
            content='聊天的标题',
            parent=self
        )

        self.temperature_card = DoubleSpinBoxSettingCard(
            FluentIcon.VPN,
            'Temperature（随机性）',
            FloatConfigItemProxy(),
            '设置当前聊天的 Temperature 值',
            self.group
        )

        self.max_tokens_card = SpinBoxSettingCard(
            FluentIcon.VPN,
            '单次回复限制',
            FloatConfigItemProxy(),
            '单次交互所用的最大 Token 数',
            self.group
        )

        self.history_count_card = SpinBoxSettingCard(
            FluentIcon.VPN,
            '附带历史消息数',
            FloatConfigItemProxy(),
            '每次请求携带的历史消息数',
            self.group
        )

        self.system_card = TextCard(
            FluentIcon.VPN,
            '系统提示词',
            ConfigItemProxy(),
            '用于限定当前会话的角色背景等',
            self.group
        )

        self.group.addSettingCard(self.name_card)
        self.group.addSettingCard(self.temperature_card)
        self.group.addSettingCard(self.max_tokens_card)
        self.group.addSettingCard(self.history_count_card)
        self.group.addSettingCard(self.system_card)

        self.expand_layout.addWidget(self.group)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    cssa = ChatSettingScrollArea()
    cssa.show()

    app.exec_()
