import os

RECORD_LOG = True
DEBUG = True

CONFIG_ROOT = os.path.expanduser('~/fingertips')
DB_PATH = os.path.join(CONFIG_ROOT, 'data.db')


OPENAI_INFO = {
    'url': os.getenv('URL'),
    'api_key': os.getenv('API_KEY')
}
