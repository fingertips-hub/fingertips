import qfluentwidgets


class LineEditSettingCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, config_item, is_password=False,
                 content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_item = config_item

        if is_password:
            self.line_edit = qfluentwidgets.PasswordLineEdit(self)
        else:
            self.line_edit = qfluentwidgets.LineEdit(self)
        self.line_edit.setMinimumWidth(300)
        self.line_edit.setText(config_item.value)
        self.hBoxLayout.addWidget(self.line_edit)
        self.hBoxLayout.addSpacing(16)

        self.line_edit.editingFinished.connect(self.line_edit_finished)

    def line_edit_finished(self):
        qfluentwidgets.qconfig.set(self.config_item, self.line_edit.text().strip())


class DoubleSpinBoxSettingCard(qfluentwidgets.SettingCard):
    def __init__(self, icon, title, config_item, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_item = config_item

        self.spin_box = qfluentwidgets.DoubleSpinBox(self)
        self.spin_box.setValue(config_item.value)
        self.spin_box.setRange(*self.config_item.range)
        self.spin_box.setSingleStep(0.1)
        self.hBoxLayout.addWidget(self.spin_box)
        self.hBoxLayout.addSpacing(16)

        self.spin_box.valueChanged.connect(self.spin_box_value_changed)

    def spin_box_value_changed(self, value):
        qfluentwidgets.qconfig.set(self.config_item, value)
