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


class AddModelMessageBox(qfluentwidgets.MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_label = qfluentwidgets.SubtitleLabel('添加模型', self)
        self.model_edit = qfluentwidgets.LineEdit(self)
        self.model_edit.setPlaceholderText('请输入需要添加的模型名称')
        self.model_edit.setClearButtonEnabled(True)

        self.viewLayout.addWidget(self.title_label)
        self.viewLayout.addWidget(self.model_edit)

        self.yesButton.setText('添加')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        self.model_edit.textChanged.connect(self.model_edit_text_changed)

    def model_edit_text_changed(self, text):
        self.yesButton.setDisabled(not bool(text.strip()))


class ModelListCard(qfluentwidgets.ExpandGroupSettingCard):
    model_changed = QtCore.Signal(str)
    model_added = QtCore.Signal(str)

    def __init__(self, icon, title, models, current_model='', content=None, message_box_parent=None,
                 parent=None):
        super().__init__(icon, title, content, parent)
        self.message_box_parent = message_box_parent

        self.choice_label = qfluentwidgets.BodyLabel(self)
        self.addWidget(self.choice_label)

        self.radio_widget = QtWidgets.QWidget(self.view)
        self.radio_layout = QtWidgets.QVBoxLayout(self.radio_widget)
        self.radio_layout.setSpacing(12)
        self.radio_layout.setAlignment(QtCore.Qt.AlignTop)
        self.radio_layout.setContentsMargins(48, 18, 0, 18)
        self.radio_layout.setSizeConstraint(
            QtWidgets.QVBoxLayout.SetMinimumSize)

        self.button_group = QtWidgets.QButtonGroup(self)
        self.button_group.buttonClicked.connect(self._radio_button_clicked)

        for model in models:
            radio = qfluentwidgets.RadioButton(model, self.radio_widget)
            self.button_group.addButton(radio)
            self.radio_layout.addWidget(radio)
            if model == current_model:
                radio.setChecked(True)

        self.add_model_widget = QtWidgets.QWidget(self.view)
        self.add_model_layout = QtWidgets.QHBoxLayout(self.add_model_widget)

        self.add_model_label = qfluentwidgets.BodyLabel(self.add_model_widget)
        self.add_model_label.setText('添加自定义模型')
        self.add_model_button = qfluentwidgets.PushButton(self.add_model_widget)
        self.add_model_button.setText('添加')
        self.add_model_button.clicked.connect(self._add_model_button_clicked)

        self.add_model_layout.setContentsMargins(48, 10, 40, 10)
        self.add_model_layout.addWidget(self.add_model_label, 0, QtCore.Qt.AlignLeft)
        self.add_model_layout.addWidget(self.add_model_button, 0, QtCore.Qt.AlignRight)
        self.add_model_layout.setSizeConstraint(QtWidgets.QHBoxLayout.SetMinimumSize)

        self.choice_label.setText(self.button_group.checkedButton().text())
        self.choice_label.adjustSize()

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radio_widget)
        self.addGroupWidget(self.add_model_widget)

    def _radio_button_clicked(self, button):
        self.choice_label.setText(button.text())
        self.model_changed.emit(button.text())

    def _adjust_view_size(self):
        """ adjust view size """
        h = self.viewLayout.sizeHint().height() + self.add_model_widget.height()
        self.spaceWidget.setFixedHeight(h)

        if self.isExpand:
            self.setFixedHeight(self.card.height() + h)

    def _add_model_button_clicked(self):
        w = AddModelMessageBox(self.message_box_parent)
        if w.exec():
            model = w.model_edit.text().strip()
            radio = qfluentwidgets.RadioButton(model, self.radio_widget)
            self.button_group.addButton(radio)
            self.radio_layout.addWidget(radio)
            self.model_added.emit(model)
            self._adjust_view_size()


class SettingPage(qfluentwidgets.ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_widget()

    def _init_widget(self):
        self.setObjectName('setting_page')

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(10, 10, 10, 20)
        self.setWidgetResizable(True)

        self.scroll_widget = QtWidgets.QWidget()
        self.expand_layout = qfluentwidgets.ExpandLayout(self.scroll_widget)
        self.setWidget(self.scroll_widget)

        self.shortcut_group = qfluentwidgets.SettingCardGroup('自定义快捷键', self.scroll_widget)
        self.main_window_card = LineEditSettingCard(
            FluentIcon.FIT_PAGE,
            '主窗口快捷键',
            'ctrl+`',
            content='呼出主窗口的快捷键',
            parent=self.shortcut_group
        )

        self.menu_window_card = LineEditSettingCard(
            FluentIcon.MENU,
            '快捷菜单快捷键',
            'F8',
            content='呼出快捷菜单的快捷键',
            parent=self.shortcut_group
        )

        self.ai_group = qfluentwidgets.SettingCardGroup('全局AI设置', self.scroll_widget)
        self.openai_base_card = LineEditSettingCard(
            FluentIcon.VPN,
            'OpenAI 代理地址',
            'https://oneapi.gptnb.me/v1',
            content='必须包含 http(s)://',
            parent=self.ai_group
        )
        self.openai_key_card = LineEditSettingCard(
            FluentIcon.VPN,
            'OpenAI API Key',
            is_password=True,
            content='使用自己的 OpenAI Key',
            parent=self.ai_group
        )
        self.default_model_card = ModelListCard(
            FluentIcon.VPN,
            '默认模型',
            ['gpt-4o', 'gpt-3.5-turbo'],
            'gpt-4o',
            content='可用的模型列表，设置模型会在模型会作为默认模型',
            message_box_parent=self,
            parent=self.ai_group
        )
        self.default_temperature_card = SpinBoxSettingCard(
            FluentIcon.VPN,
            '默认 Temperature',
            0.6,
            '设置默认 Temperature 值',
            self.ai_group
        )

        self.update_group = qfluentwidgets.SettingCardGroup('软件更新', self.scroll_widget)
        self.update_on_start_up_card = qfluentwidgets.SwitchSettingCard(
            FluentIcon.UPDATE,
            '在软件启动时检查更新',
            '新版本将更加稳定并拥有更多功能（建议启动此选项）',
            parent=self.update_group
        )

        self.about_group = qfluentwidgets.SettingCardGroup('关于', self.scroll_widget)
        self.help_card = qfluentwidgets.PrimaryPushSettingCard(
            '打开帮助文档',
            FluentIcon.HELP,
            '帮助',
            '发现新功能并了解有关 Fingertips 的使用技巧',
            self.about_group
        )
        self.feedback_card = qfluentwidgets.PrimaryPushSettingCard(
            '提供反馈',
            FluentIcon.FEEDBACK,
            '反馈',
            '通过提供反馈帮助我们改进 Fingertips',
            self.about_group
        )
        self.about_card = qfluentwidgets.PrimaryPushSettingCard(
            '检查更新',
            FluentIcon.INFO,
            '关于',
            '© 版权所有 2024, LiaoKong, 当前版本 0.0.1'
        )

        self.shortcut_group.addSettingCard(self.main_window_card)
        self.shortcut_group.addSettingCard(self.menu_window_card)

        self.ai_group.addSettingCard(self.openai_base_card)
        self.ai_group.addSettingCard(self.openai_key_card)
        self.ai_group.addSettingCard(self.default_model_card)
        self.ai_group.addSettingCard(self.default_temperature_card)

        self.update_group.addSettingCard(self.update_on_start_up_card)

        self.about_group.addSettingCard(self.help_card)
        self.about_group.addSettingCard(self.feedback_card)
        self.about_group.addSettingCard(self.about_card)

        self.expand_layout.setSpacing(20)
        self.expand_layout.setContentsMargins(10, 8, 20, 0)
        self.expand_layout.addWidget(self.shortcut_group)
        self.expand_layout.addWidget(self.ai_group)
        self.expand_layout.addWidget(self.update_group)
        self.expand_layout.addWidget(self.about_group)

        self.setStyleSheet(
            'QScrollArea {border: none; background:transparent}'
        )
