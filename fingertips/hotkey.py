import sys
import ctypes
import ctypes.wintypes

from PySide2 import QtCore

ALT = 1
CONTROL = 2
SHIFT = 4
WIN = 8
WM_HOTKEY = 786

mod_keys = {'ctrl': CONTROL, 'alt': ALT, 'shift': SHIFT}

# msdn.microsoft.com/en-us/library/dd375731
# http://www.kbdedit.com/manual/low_level_vk_list.html
code_by_vk = {
    'f1': 0x70,
    'f2': 0x71,
    'f3': 0x72,
    'f4': 0x73,
    'f5': 0x74,
    'f6': 0x75,
    'f7': 0x76,
    'f8': 0x77,
    'f9': 0x78,
    'f10': 0x79,
    'f11': 0x7A,
    'f12': 0x7B,
    '`': 0xC0,
}


class HotkeyThread(QtCore.QThread):
    show_main_sign = QtCore.Signal()
    shortcut_triggered = QtCore.Signal(str)

    def __init__(self, key_map, parent=None):
        super(HotkeyThread, self).__init__(parent=parent)
        self.key_map = key_map
        self.registered_hotkeys = []  # 保存注册的热键ID
        self.running = True
        self.thread_id = None  # 保存线程ID

    def stop(self):
        """停止线程并清理热键"""
        self.running = False
        # 立即清理热键注册
        user32 = ctypes.windll.user32
        for hotkey_id in self.registered_hotkeys:
            try:
                user32.UnregisterHotKey(None, hotkey_id)
            except Exception:
                pass
        # 发送退出消息来停止消息循环
        try:
            ctypes.windll.user32.PostQuitMessage(0)
            # 如果有线程ID，向线程发送退出消息
            if self.thread_id:
                ctypes.windll.user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)  # WM_QUIT
        except Exception:
            pass

    def run(self):
        # 保存当前线程ID用于退出时发送消息
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        
        user32 = ctypes.windll.user32
        param_map = {}
        try:
            param = 369
            for key in self.key_map:
                param += 1
                callback_name = self.key_map[key]
                keys = key.split('+')
                fk = 0
                if len(keys) > 1:
                    fk = sum([mod_keys[key.lower()] for key in keys[:-1]])
                vk = code_by_vk.get(keys[-1].lower())
                if not vk:
                    vk = ord(keys[-1])
                user32.RegisterHotKey(None, param, fk, vk)
                param_map[param] = callback_name
                self.registered_hotkeys.append(param)  # 保存热键ID
        except BaseException as e:
            sys.exit()
        try:
            msg = ctypes.wintypes.MSG()
            while self.running and user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    param = int(msg.wParam)
                    if param in param_map:
                        if not param_map[param]:  # main hotkey
                            self.show_main_sign.emit()
                        else:
                            self.shortcut_triggered.emit(param_map[param])
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageA(ctypes.byref(msg))
        finally:
            # 清理所有注册的热键
            for hotkey_id in self.registered_hotkeys:
                user32.UnregisterHotKey(None, hotkey_id)
