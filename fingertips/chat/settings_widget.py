import qframelesswindow
from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

import qfluentwidgets
from qfluentwidgets import FluentIcon

from fingertips.common_widgets import LineEditSettingCard as _LineEditSettingCard
from fingertips.common_widgets import DoubleSpinBoxSettingCard as _DoubleSpinBoxSettingCard
from fingertips.settings.config_model import config_model


class LineEditSettingCard(_LineEditSettingCard):
    def line_edit_finished(self):
        self.config_item.value = self.line_edit.text().strip()


class DoubleSpinBoxSettingCard(_DoubleSpinBoxSettingCard):
    def spin_box_value_changed(self, value):
        self.config_item.value = self.spin_box.value()


class SpinBoxSettingCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, config_item, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_item = config_item

        self.spin_box = qfluentwidgets.SpinBox(self)
        self.spin_box.setRange(*config_item.range)
        self.spin_box.setValue(config_item.value)
        self.hBoxLayout.addWidget(self.spin_box)
        self.hBoxLayout.addSpacing(16)

        self.spin_box.valueChanged.connect(self.spin_box_value_changed)

    def spin_box_value_changed(self, value):
        self.config_item.value = self.spin_box.value()


class ComboBoxCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, config_item, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_item = config_item

        self.combo_box = qfluentwidgets.ComboBox()
        self.combo_box.addItems(config_model.openai_models.value)
        self.combo_box.setCurrentText(self.config_item.value)
        self.hBoxLayout.addWidget(self.combo_box)
        self.hBoxLayout.addSpacing(16)

        self.combo_box.currentIndexChanged.connect(self.combo_box_changed)

    def combo_box_changed(self):
        self.config_item.value = self.combo_box.currentText()


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

        self.text_edit.textChanged.connect(self.text_edit_changed)

    def text_edit_changed(self):
        self.config_item.value = self.text_edit.toPlainText().strip()


class ChatSettingScrollArea(qfluentwidgets.ScrollArea):
    def __init__(self, chat_model, parent=None):
        super().__init__(parent)
        self.chat_model = chat_model

        self.setStyleSheet('border: 0px solid transparent;')

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
            self.chat_model.label,
            content='聊天的标题',
            parent=self
        )

        self.model_card = ComboBoxCard(
            FluentIcon.VPN,
            '模型',
            self.chat_model.model,
            content='会话中所使用的模型',
            parent=self
        )

        self.temperature_card = DoubleSpinBoxSettingCard(
            FluentIcon.VPN,
            'Temperature（随机性）',
            self.chat_model.temperature,
            '设置当前聊天的 Temperature 值',
            self.group
        )

        self.max_tokens_card = SpinBoxSettingCard(
            FluentIcon.VPN,
            '单次回复限制',
            self.chat_model.max_tokens,
            '单次交互所用的最大 Token 数',
            self.group
        )

        self.history_count_card = SpinBoxSettingCard(
            FluentIcon.VPN,
            '附带历史消息数',
            self.chat_model.history_count,
            '每次请求携带的历史消息数',
            self.group
        )

        self.system_card = TextCard(
            FluentIcon.VPN,
            '系统提示词',
            self.chat_model.system,
            '用于限定当前会话的角色背景等',
            self.group
        )

        self.group.addSettingCard(self.name_card)
        self.group.addSettingCard(self.model_card)
        self.group.addSettingCard(self.temperature_card)
        self.group.addSettingCard(self.max_tokens_card)
        self.group.addSettingCard(self.history_count_card)
        self.group.addSettingCard(self.system_card)

        self.expand_layout.addWidget(self.group)


class ChatSettingDialog(qframelesswindow.AcrylicWindow):
    closed = QtCore.Signal()

    def __init__(self, chat_model, parent=None):
        super().__init__(parent)

        self.resize(600, 550)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.setTitleBar(qframelesswindow.StandardTitleBar(self))
        self.titleBar.setIcon(QtGui.QIcon('res/icon.png'))
        self.titleBar.setTitle('当前会话配置')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 26, 10, 10)

        self.setting_scroll_area = ChatSettingScrollArea(chat_model)
        layout.addWidget(self.setting_scroll_area)

        qfluentwidgets.FluentStyleSheet.DIALOG.apply(self)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    cssa = ChatSettingDialog(None)
    cssa.show()

    app.exec_()
