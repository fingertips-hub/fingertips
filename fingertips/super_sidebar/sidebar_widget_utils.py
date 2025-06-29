import pkgutil
import inspect
import importlib

from PySide2 import QtWidgets, QtCore
from fingertips.widget_utils import signal_bus


class SidebarWidget(QtWidgets.QWidget):
    name = None
    category = None
    icon = None
    description = ''

    save_config_signal = QtCore.Signal()
    __WIDGET_TYPE__ = 'widget'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit_mode = False
        self._check_base_info()
        signal_bus.super_sidebar_edit_mode_changed.connect(self.edit_mode_changed)

        # 设置大小策略，允许组件在两个方向上扩展
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def _check_base_info(self):
        if not self.name:
            raise ValueError('Widget name is not set')

        if not self.category:
            raise ValueError('Widget category is not set')

    def edit_mode_changed(self, edit_mode):
        self.edit_mode = edit_mode

    def get_config(self):
        return {}

    def set_config(self, config):
        pass


def discover_sidebar_widgets():
    widgets = []
    module_path = 'fingertips.sidebar_widgets'
    main_module = importlib.import_module(module_path)
    for importer, modname, ispkg in pkgutil.iter_modules(main_module.__path__, module_path + '.'):
        submodule = importlib.import_module(modname)

        for name, cls in inspect.getmembers(submodule, inspect.isclass):
            if cls.__module__ == modname:
                if hasattr(cls, '__WIDGET_TYPE__'):
                    widgets.append(cls)

    return widgets


if __name__ == '__main__':
    widgets = discover_sidebar_widgets()
    for widget in widgets:
        print(widget)
