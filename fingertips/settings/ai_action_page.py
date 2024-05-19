from functools import partial

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

import qframelesswindow
import qfluentwidgets
from qfluentwidgets import FluentIcon

from fingertips.settings.config_model import config_model
from fingertips.db_utils import AIActionDB


class AIActionType:
    PRESET = 'preset'


class AIActionCard(qfluentwidgets.CardWidget):
    edited = QtCore.Signal(dict)
    deleted = QtCore.Signal(dict)
    enabled_changed = QtCore.Signal(dict)

    def __init__(self, title, content, enabled, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.title = title

        self.title_label = qfluentwidgets.BodyLabel(title, self)
        self.content_label = qfluentwidgets.CaptionLabel(content, self)
        self.more_button = qfluentwidgets.TransparentToolButton(FluentIcon.MORE, self)
        self.more_button.setFixedSize(32, 32)
        self.more_button.clicked.connect(self.more_button_clicked)

        self.enable_button = qfluentwidgets.SwitchButton(self)
        self.enable_button.setOnText('启用')
        self.enable_button.setOffText('停用')
        self.enable_button.setChecked(enabled)
        self.enable_button.checkedChanged.connect(self.enable_button_checked)

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
        edit_action = qfluentwidgets.Action(FluentIcon.EDIT, '编辑', self)
        edit_action.triggered.connect(partial(self.action_triggered, 'edit'))
        menu.addAction(edit_action)

        delete_action = qfluentwidgets.Action(FluentIcon.DELETE, '删除', self)
        delete_action.triggered.connect(partial(self.action_triggered, 'delete'))
        menu.addAction(delete_action)

        x = (self.more_button.width() - menu.width()) // 2 + 10
        pos = self.more_button.mapToGlobal(QtCore.QPoint(x, self.more_button.height()))
        menu.exec(pos)

    def update_data(self, data):
        self.title_label.setText(data['name'])
        self.content_label.setText(data['description'])
        self.data = data
        self.title = data['name']

        self.update()

    def action_triggered(self, _type):
        if _type == 'edit':
            self.edited.emit(self.data)
        else:
            self.deleted.emit(self.data)

    def enable_button_checked(self, is_checked):
        self.data['enabled'] = is_checked
        self.enabled_changed.emit(self.data)


class AIActions(qfluentwidgets.ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.action_by_name = {}

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

    def add_action(self, title, content, enabled=True, data=None):
        action = AIActionCard(title, content, enabled, data, self)
        self._layout.addWidget(action)

        self.action_by_name[title] = action
        return action

    def remove_action(self, name):
        action = self.action_by_name[name]
        self._layout.removeWidget(action)
        action.deleteLater()

    def update_action(self, name, data):
        action = self.action_by_name[name]
        action.update_data(data)


class AddPresetForm(qframelesswindow.FramelessDialog):
    def __init__(self, info=None, parent=None):
        super().__init__(parent)
        self.info = info or {}
        self.db = AIActionDB()
        self.resize(600, 600)

        self.title_label = qfluentwidgets.SubtitleLabel(
            f'{"编辑" if self.info else "添加"}预设', self)

        self.name_line = qfluentwidgets.LineEdit()
        self.description_line = qfluentwidgets.LineEdit()
        self.models_combobox = qfluentwidgets.ComboBox(self)

        self.temperature_line = qfluentwidgets.DoubleSpinBox(self)
        self.temperature_line.setSingleStep(0.1)

        self.max_tokens_line = qfluentwidgets.SpinBox(self)
        self.prompt_line = qfluentwidgets.PlainTextEdit(self)
        self.prompt_line.setPlaceholderText('请输入预设提示词，传入的内容请使用：{{TEXT}}')

        layout = QtWidgets.QGridLayout()

        layout.addWidget(qfluentwidgets.BodyLabel('名称: ', self), 0, 0)
        layout.addWidget(self.name_line, 0, 1)

        layout.addWidget(qfluentwidgets.BodyLabel('描述: ', self), 1, 0)
        layout.addWidget(self.description_line, 1, 1)

        layout.addWidget(qfluentwidgets.BodyLabel('模型: ', self), 2, 0)
        layout.addWidget(self.models_combobox, 2, 1)

        layout.addWidget(qfluentwidgets.BodyLabel('温度: ', self), 3, 0)
        layout.addWidget(self.temperature_line, 3, 1)

        layout.addWidget(qfluentwidgets.BodyLabel('最大 Token: ', self), 4, 0)
        layout.addWidget(self.max_tokens_line, 4, 1)

        layout.addWidget(qfluentwidgets.BodyLabel('提示词: ', self), 5, 0)
        layout.addWidget(self.prompt_line, 5, 1)

        self.save_button = qfluentwidgets.PrimaryPushButton('保存', self)
        self.save_button.setMinimumWidth(120)
        self.save_button.clicked.connect(self.save_button_clicked)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.addWidget(self.title_label, 0, QtCore.Qt.AlignLeft)
        main_layout.addLayout(layout)
        main_layout.addWidget(self.save_button, 0, QtCore.Qt.AlignRight)

        qfluentwidgets.FluentStyleSheet.DIALOG.apply(self)

        desktop = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def save_button_clicked(self):
        name = self.name_line.text().strip()
        if not name:
            return self.show_message('名称')

        action = self.db.get_action(name)
        if action and self.info.get('name') != name:
            return self.show_message(f'名称 “{name}” 已存在！', True)

        description = self.description_line.text().strip()
        if not description:
            return self.show_message('描述')

        model = self.models_combobox.currentText()
        temperature = self.temperature_line.value()
        max_tokens = self.max_tokens_line.value()
        prompt = self.prompt_line.toPlainText().strip()
        if not prompt:
            return self.show_message('提示词')

        self.info = {
            'name': name,
            'description': description,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'prompt': prompt
        }

        self.close()

    def show_message(self, content, overwrite=False):
        return qfluentwidgets.InfoBar.error(
            '错误',
            f'请先设置 ”{content}“ 字段！' if not overwrite else content,
            duration=2000,
            parent=self
        )

    def exec_(self):
        self.name_line.setText(self.info.get('name', ''))
        self.description_line.setText(self.info.get('description', ''))

        self.models_combobox.addItems(config_model.openai_models.value)
        self.models_combobox.setCurrentText(
            self.info.get('model', config_model.openai_current_model.value))

        self.temperature_line.setRange(*config_model.openai_temperature.range)
        self.temperature_line.setValue(
            self.info.get('temperature', config_model.openai_temperature.value))

        self.max_tokens_line.setValue(self.info.get('max_tokens', 0))
        self.prompt_line.setPlainText(self.info.get('prompt', ''))

        super().exec_()


class AIActionPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = AIActionDB()
        self.setObjectName('ai_action_page')

        self.button_menu = qfluentwidgets.RoundMenu(parent=self)
        preset_action = qfluentwidgets.Action(FluentIcon.ROBOT, '预设', self)
        preset_action.triggered.connect(self.preset_action_triggered)
        self.button_menu.addAction(preset_action)

        self.add_button = qfluentwidgets.PrimaryDropDownPushButton(FluentIcon.ADD, '添加', self)
        self.add_button.setMenu(self.button_menu)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 20, 0)
        header_layout.addWidget(self.add_button, 0, QtCore.Qt.AlignRight)

        self.ai_actions = AIActions(self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(10, 16, 12, 16)
        layout.addLayout(header_layout)
        layout.addWidget(self.ai_actions)

        for action in self.db.get_actions():
            action = self.ai_actions.add_action(
                action['name'],
                action['description'],
                action['enabled'],
                action
            )
            action.edited.connect(self._action_edit)
            action.deleted.connect(self._action_delete)
            action.enabled_changed.connect(self._action_enabled_changed)

    def _action_enabled_changed(self, data):
        self.db.update_action(data)

    def _action_edit(self, data):
        apf = AddPresetForm(data, parent=self)
        apf.exec_()

        if data['name'] == apf.info['name']:
            new_data = data
            self.db.update_action(data)
        else:
            new_data = apf.info
            new_data.update({'enabled': data['enabled'], 'type': data['type']})
            self.db.delete_action(data['name'])
            self.db.add_action(new_data)

        self.ai_actions.update_action(data['name'], new_data)

    def _action_delete(self, data):
        w = qfluentwidgets.Dialog('删除', f'你确定要删除 {data["name"]} ？', self)
        if w.exec():
            self.ai_actions.remove_action(data['name'])
            self.db.delete_action(data['name'])
            return qfluentwidgets.InfoBar.success(
                '提示', f'{data["name"]} 删除成功！', duration=1500, parent=self)

    def preset_action_triggered(self):
        apf = AddPresetForm(parent=self)
        apf.exec_()
        if not apf.info:
            return

        data = apf.info
        data.update({'type': AIActionType.PRESET, 'enabled': True})
        self.db.add_action(data)

        action = self.ai_actions.add_action(data['name'], data['description'], data=data)
        action.edited.connect(self._action_edit)
        action.deleted.connect(self._action_delete)
        action.enabled_changed.connect(self._action_enabled_changed)

        return qfluentwidgets.InfoBar.success(
            '提示', f'{data["name"]} 已成功添加！', duration=1500, parent=self)
