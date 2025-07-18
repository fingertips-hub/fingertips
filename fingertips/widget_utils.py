from PySide2 import QtCore


class SignalBus(QtCore.QObject):
    """ 全局事件总线 """

    chat_item_clicked = QtCore.Signal(object)
    chat_item_edited = QtCore.Signal(object)
    chat_item_deleted = QtCore.Signal()
    super_sidebar_config_changed = QtCore.Signal(dict)
    super_sidebar_edit_mode_changed = QtCore.Signal(bool)

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(SignalBus, cls).__new__(cls, *args, **kwargs)

        return cls._instance


signal_bus = SignalBus()
