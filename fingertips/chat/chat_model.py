import uuid
from PySide2 import QtCore

from fingertips.db_utils import ChatDB


class ChatConfigItem(QtCore.QObject):
    value_changed = QtCore.Signal(dict)

    def __init__(self, key, default):
        super().__init__()
        self.key = key
        self._value = default

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self.value_changed.emit(self.dict())

    def dict(self):
        return {self.key: self._value}


class ChatConfigRangeItem(ChatConfigItem):
    def __init__(self, key, default, range_):
        super().__init__(key, default)
        self.range = range_


class ChatConfigModel(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self._db_client = None
        self._ignore_value_changed = False

        self.id = ChatConfigItem('id', str(uuid.uuid4()))
        self.label = ChatConfigItem('label', '新聊天')
        self.temperature = ChatConfigRangeItem('temperature', 0.6, (0, 2))
        self.max_tokens = ChatConfigItem('max_tokens', 4096)
        self.history_count = ChatConfigItem('history_count', 4)
        self.system = ChatConfigItem('system', '')
        self.model = ChatConfigItem('model', 'gpt-4o')
        self.histories = ChatConfigItem('histories', [])

        self.load_fields()

    def load_fields(self):
        self._items = {}
        for name in dir(self):
            item = getattr(self, name)
            if not isinstance(item, ChatConfigItem):
                continue

            item.value_changed.connect(self._item_value_changed)
            self._items.update(item.dict())

    def _item_value_changed(self, data):
        self._items.update(data)
        # todo 保存到 db
        if not self._db_client:
            return

        if self._ignore_value_changed:
            return

    def from_db(self, data, db):
        self._db_client = db
        self._ignore_value_changed = True

        for key, value in data.items():
            item = getattr(self, key)
            item.value = value

        self._ignore_value_changed = False

    def dict(self):
        return self._items


if __name__ == '__main__':
    cm = ChatConfigModel()
    cm.from_db({'label': '测试聊天', 'temperature': 2, 'system': 'yyyyy'}, None)
    print(cm.dict())

    # cm.label.value = 'aa'
    # print(cm._items)
    #
    # bb = ChatConfigModel()
    # print(bb.label.value)
