import os

import pkgutil
from fingertips.utils import get_logger
from fingertips.core import AbstractBase

log = get_logger('注册action')


class ActionRegister(object):
    def __init__(self, main_window):
        self.main_window = main_window
        self._load_actions()
        log.info(u'action已加载完成')
        log.info(self._actions_storage)

    def _load_actions(self):
        self._actions_storage = {}
        for importer, package_name, _ in pkgutil.iter_modules(
                [os.path.join(os.path.dirname(os.path.dirname(__file__)), 'actions')]):
            module = importer.find_module(package_name).load_module(package_name)
            for cls_str in dir(module):
                class_obj = getattr(module, cls_str)
                if hasattr(class_obj, 'need_register'):
                    obj = class_obj()
                    obj.main_window = self.main_window
                    for action_type in obj.action_types:
                        self._actions_storage.setdefault(action_type, []).append(obj)

    def get_actions(self, action_type):
        return self._actions_storage.get(action_type, [])

    def reload_actions(self):
        self._load_actions()
        log.info(u'action已成功重新加载')
        log.info(self._actions_storage)


EMPTY = 0
TEXT = 1
MULT_FILES = 2
FILE = 3


class AbstractAction(AbstractBase):
    title = ''
    icon = ''
    description = ''
    action_types = []
    exts = []

    _verify_fields = ['title', 'description', 'action_types']

    def run(self, files):
        raise NotImplementedError
