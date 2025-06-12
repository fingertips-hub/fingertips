import qfluentwidgets
from qfluentwidgets import FluentIcon
from PySide2 import QtCore, QtWidgets

from fingertips.widget_utils import signal_bus
from fingertips.settings.config_model import config_model
from fingertips.common_widgets import DoubleSpinBoxSettingCard, SpinBoxSettingCard, FolderPathSettingCard


class SuperSideBarPage(qfluentwidgets.ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_widget()

    def init_widget(self):
        self.setObjectName('supper_sidebar_page')

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(10, 10, 10, 20)
        self.setWidgetResizable(True)

        self.content_widget = QtWidgets.QWidget()
        self.content_layout = qfluentwidgets.ExpandLayout(self.content_widget)
        self.setWidget(self.content_widget)

        self.settings_group = qfluentwidgets.SettingCardGroup('基础设置', self.content_widget)
        self.enable_card = qfluentwidgets.SwitchSettingCard(
            FluentIcon.ACCEPT,
            '启用',
            '启用超级侧栏',
            config_model.enable_super_sidebar,
            self.settings_group
        )
        config_model.enable_super_sidebar.valueChanged.connect(
            lambda: signal_bus.super_sidebar_config_changed.emit(
                {'enable': config_model.enable_super_sidebar.value})
        )

        self.type_card = qfluentwidgets.OptionsSettingCard(
            config_model.super_sidebar_type,
            FluentIcon.PHOTO,
            '样式类型',
            '设置超级侧栏样式类型',
            ['亚克力磨砂', '半透明'],
            self.settings_group,
        )
        config_model.super_sidebar_type.valueChanged.connect(self.type_card_changed)

        self.opacity_card = DoubleSpinBoxSettingCard(
            FluentIcon.CONSTRACT,
            '不透明度',
            config_model.super_sidebar_opacity,
            '设置超级侧栏背景不透明度',
            self.settings_group
        )
        config_model.super_sidebar_opacity.valueChanged.connect(
            lambda: signal_bus.super_sidebar_config_changed.emit(
                {'opacity': config_model.super_sidebar_opacity.value})
        )

        self.position_card = qfluentwidgets.OptionsSettingCard(
            config_model.super_sidebar_position,
            FluentIcon.MOVE,
            '位置',
            '设置超级侧栏出现位置',
            ['左', '右'],
            self.settings_group,
        )
        config_model.super_sidebar_position.valueChanged.connect(
            lambda: signal_bus.super_sidebar_config_changed.emit(
                {'position': config_model.super_sidebar_position.value})
        )

        self.plugin_path_card = FolderPathSettingCard(
            FluentIcon.FOLDER,
            '插件路径',
            config_model.super_sidebar_plugin_path,
            '设置超级侧栏插件路径',
            self.settings_group,
        )

        self.settings_group.addSettingCard(self.enable_card)
        self.settings_group.addSettingCard(self.type_card)
        self.settings_group.addSettingCard(self.opacity_card)
        self.settings_group.addSettingCard(self.position_card)
        self.settings_group.addSettingCard(self.plugin_path_card)

        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(10, 8, 20, 0)
        self.content_layout.addWidget(self.settings_group)

        self.setStyleSheet(
            'QScrollArea {border: none; background:transparent}'
        )

        self.type_card_changed()

    def type_card_changed(self):
        if config_model.super_sidebar_type.value == 'acrylic':
            self.opacity_card.hide()
            self.opacity_card.setEnabled(False)
        else:
            self.opacity_card.show()
            self.opacity_card.setEnabled(True)

        signal_bus.super_sidebar_config_changed.emit(
            {'type': config_model.super_sidebar_type.value})
