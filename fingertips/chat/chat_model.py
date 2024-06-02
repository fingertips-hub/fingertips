import uuid
import json

from PySide2 import QtCore

from fingertips.settings.config_model import config_model


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


class ChatConfigListItem(ChatConfigItem):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        is_init = False
        if isinstance(v, str):
            v = json.loads(v)
            is_init = True

        self._value = v

        if not is_init:
            self.value_changed.emit(self.dict())

    def dict(self):
        return {self.key: json.dumps(self._value)}


class ChatConfigModel(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self._db_client = None
        self._ignore_value_changed = False

        self.cid = ChatConfigItem('cid', str(uuid.uuid4()))
        self.label = ChatConfigItem('label', '新聊天')
        self.temperature = ChatConfigRangeItem('temperature', config_model.openai_temperature.value, (0, 2))
        self.max_tokens = ChatConfigRangeItem('max_tokens', 0, (0, 20000))
        self.history_count = ChatConfigRangeItem('history_count', 4, (0, 99))
        self.system = ChatConfigItem('system', '')
        self.model = ChatConfigItem('model', config_model.openai_current_model.value)
        self.histories = ChatConfigListItem('histories', [])

        self.load_fields()

    def load_fields(self):
        for name in dir(self):
            item = getattr(self, name)
            if not isinstance(item, ChatConfigItem):
                continue

            item.value_changed.connect(self._item_value_changed)

    def _item_value_changed(self, data):
        if self._ignore_value_changed:
            return

        self._db_client.update_chat(self.dict())

    def from_db(self, data, db):
        self._db_client = db
        self._ignore_value_changed = True

        for key, value in data.items():
            if not hasattr(self, key):
                continue

            item = getattr(self, key)
            item.value = value

        self._ignore_value_changed = False

    def dict(self):
        items = {}
        for name in dir(self):
            item = getattr(self, name)
            if not isinstance(item, ChatConfigItem):
                continue

            items.update(item.dict())
        return items

    def save(self, db):
        self._db_client = db
        self._db_client.add_chat(self.dict())


if __name__ == '__main__':
    cm = ChatConfigModel()
    cm.from_db({'label': '测试聊天', 'temperature': 2, 'system': 'yyyyy'}, None)
    print(cm.dict())

    # cm.label.value = 'aa'
    # print(cm._items)
    #
    # bb = ChatConfigModel()
    # print(bb.label.value)
