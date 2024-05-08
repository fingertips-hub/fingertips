import os

RECORD_LOG = True
DEBUG = True

GLOBAL_HOTKEYS = {
    'ctrl+`': '',
    'F8': 'show_menus'
}

DB_PATH = os.path.expanduser('~/fingertips/data.db')


OPENAI_INFO = {
    'url': os.getenv('URL'),
    'api_key': os.getenv('API_KEY')
}
