import os
import sys
import logging
from ctypes import windll
from logging.handlers import TimedRotatingFileHandler

from PySide2 import QtWidgets
import pyautogui
import win32com.client

from fingertips.config import RECORD_LOG, DEBUG

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


class SingleLogger(object):
    log_path = './log/Fingertips.log'
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))

    log = logging.getLogger('Fingertips')
    log.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(plugin_name)s - %(levelname)s - %(message)s')
    log_file_handler = TimedRotatingFileHandler(
        filename=log_path, when='D', encoding='utf-8')
    log_file_handler.setFormatter(formatter)
    log_file_handler.setLevel(logging.INFO)
    log.addHandler(log_file_handler)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    def __init__(self, name='Fingertips'):
        self.name = name

    def add_name_info(self, kwargs):
        if not kwargs:
            kwargs = {}
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['plugin_name'] = self.name
        return kwargs

    def info(self, msg, *args, **kwargs):
        kwargs = self.add_name_info(kwargs)
        self.log.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        kwargs = self.add_name_info(kwargs)
        self.log.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        kwargs = self.add_name_info(kwargs)
        self.log.error(msg, *args, **kwargs)


class EmptyLogger(object):
    def __init__(self, name):
        self.title = u'- {} - '.format(name)

    def info(self, msg, *args, **kwargs):
        if DEBUG:
            print(self.title + msg)
        return

    def warning(self, msg, *args, **kwargs):
        if DEBUG:
            print(self.title + msg)
        return

    def error(self, msg, *args, **kwargs):
        if DEBUG:
            print(self.title + msg)
        return


def get_logger(name):
    if RECORD_LOG:
        return SingleLogger(name)
    return EmptyLogger(name)


def clear_clipboard():
    if windll.user32.OpenClipboard(None):
        windll.user32.EmptyClipboard()
        windll.user32.CloseClipboard()


def get_exe_path(file_path):
    if file_path.lower().endswith('.lnk'):
        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(file_path)
        return shortcut.Targetpath

    return file_path


def get_select_entity():
    clear_clipboard()
    clipboard = QtWidgets.QApplication.clipboard()

    pyautogui.hotkey('ctrl', 'c')

    urls = clipboard.mimeData().urls()
    urls = [u.toLocalFile() for u in urls if os.path.exists(u.toLocalFile())]
    text = clipboard.mimeData().text()

    if not urls and not text:
        data = {
            'type': 'empty'
        }
    elif not urls and text:
        data = {
            'type': 'text',
            'text': text
        }
    else:
        data = {
            'type': 'urls',
            'urls': urls
        }

    return data
