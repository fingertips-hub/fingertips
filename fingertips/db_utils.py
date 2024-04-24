import os
import dataset

from fingertips.settings import DB_PATH


class SoftwareDB(object):
    def __init__(self):
        if not os.path.exists(os.path.dirname(DB_PATH)):
            os.makedirs(os.path.dirname(DB_PATH))

        self._db = dataset.connect(f'sqlite:///{DB_PATH}')
        self.table = self._db['software']

    def add_software(self, name, exe_path):
        data = self.table.find_one(exe_path=exe_path)
        if not data:
            self.table.insert({'name': name, 'exe_path': exe_path})
            return True

        return False

    def get_software(self):
        return self.table.all()


