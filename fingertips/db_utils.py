import os
import dataset

from fingertips.config import DB_PATH


class DBBase(object):
    def __init__(self):
        if not os.path.exists(os.path.dirname(DB_PATH)):
            os.makedirs(os.path.dirname(DB_PATH))

        self._db = dataset.connect(f'sqlite:///{DB_PATH}')


class SoftwareDB(DBBase):
    def __init__(self):
        super().__init__()
        self.table = self._db['software']

    def add_software(self, name, exe_path, lnk_path=''):
        data = self.table.find_one(exe_path=exe_path)
        if not data:
            self.table.insert({
                'name': name, 'exe_path': exe_path, 'lnk_path': lnk_path})
            return True

        return False

    def get_software(self):
        return self.table.all()


class AIActionDB(DBBase):
    def __init__(self):
        super().__init__()
        self.table = self._db['ai_actions']

    def add_action(self, action):
        return self.table.insert(action)

    def get_action(self, name):
        return self.table.find_one(name=name)

    def get_actions(self):
        return self.table.all()

    def delete_action(self, name):
        return self.table.delete(name=name)

    def update_action(self, data):
        return self.table.update(data, ['name'])


class CozeActionDB(AIActionDB):
    def __init__(self):
        super().__init__()
        self.table = self._db['coze_actions']


class ChatDB(DBBase):
    def __init__(self):
        super().__init__()
        self.table = self._db['chats']

    def add_chat(self, chat):
        self.table.insert(chat)
