import os
import json
import uuid
from functools import partial

from PySide2 import QtGui
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2.QtWebChannel import QWebChannel
from PySide2.QtWebEngineWidgets import QWebEngineSettings

import qfluentwidgets
from qfluentwidgets import FluentIcon
from qframelesswindow.webengine import FramelessWebEngineView

from fingertips.core.thread import AskAIThread
from fingertips.widget_utils import signal_bus
from fingertips.db_utils import ChatDB
from fingertips.chat.chat_model import ChatConfigModel
from fingertips.utils import ROOT_PATH


class BridgeObject(QtCore.QObject):
    clear_chat = QtCore.Signal()
    add_chat_item = QtCore.Signal(str)
    set_ai_chat = QtCore.Signal(str)

    def set_ai_chat_content(self, message):
        self.set_ai_chat.emit(message)

    def add_chat_item_content(self, chat_item):
        self.add_chat_item.emit(json.dumps(chat_item))

    def clear_chat_histories(self):
        self.clear_chat.emit()


class ChatHistoryWidget(FramelessWebEngineView):
    chat_response_finished = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.histories = []
        self.thread = None

        self.init_settings()

        self.channel = QWebChannel(self)
        self.bridge_object = BridgeObject()

        self.channel.registerObject('Bridge', self.bridge_object)
        self.page().setWebChannel(self.channel)
        self.load(QtCore.QUrl.fromLocalFile('{}/chat/chat.html'.format(ROOT_PATH)))

        # 直接调用而不是使用定时器，避免在对象销毁时的回调警告
        self.apply_rounded_corners()

    def init_content(self, histories):
        self.bridge_object.clear_chat_histories()

        for message in histories:
            self.bridge_object.add_chat_item_content(message)

        self.histories = histories

    def set_user_content(self, text='', chat_model=None, use_histories=False):
        if not use_histories:
            message = {
                'role': 'user',
                'content': text.strip(),
                'id': str(uuid.uuid4())
            }
            self.bridge_object.add_chat_item_content(message)

            ai_id = str(uuid.uuid4())
            self.bridge_object.add_chat_item_content({
                'role': 'assistant',
                'content': '',
                'id': ai_id
            })
        else:
            message, _ = self.histories[-2:]
            ai_id = message['id']

            self.histories = self.histories[:-2]

        self.thread = AskAIThread(
            message['content'],
            model=chat_model.model.value,
            temperature=chat_model.temperature.value,
            max_tokens=chat_model.max_tokens.value,
            system_prompt=chat_model.system.value,
            convert_markdown=False,
            histories=self.histories,
            parent=self
        )

        # 使用functools.partial替代lambda避免回调警告
        from functools import partial
        self.thread.resulted.connect(partial(self.bridge_object.set_ai_chat_content))
        self.thread.finished.connect(partial(self._thread_finished, ai_id, chat_model))
        self.thread.start()

        self.histories.append(message)
        chat_model.histories.value = self.histories

    def stop_thread(self):
        self.thread.requestInterruption()

    def _thread_finished(self, ai_id, chat_model, message):
        data = {
            'role': 'assistant',
            'content': message,
            'id': ai_id
        }
        self.histories.append(data)
        chat_model.histories.value = self.histories

        self.chat_response_finished.emit(message)

    def apply_rounded_corners(self):
        path = QtGui.QPainterPath()
        path.addRoundedRect(self.rect(), 6, 6)  # 设置圆角半径
        # 将路径转换为区域并设置为遮罩
        region = QtGui.QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    @staticmethod
    def init_settings():
        settings = QWebEngineSettings.globalSettings()
        settings.setDefaultTextEncoding('utf-8')
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.TouchIconsEnabled, True)


class ChatItem(qfluentwidgets.CardWidget):
    edited = QtCore.Signal()
    deleted = QtCore.Signal()

    def __init__(self, chat_model: ChatConfigModel, parent=None):
        super().__init__(parent)
        self.chat_model = chat_model

        self.setObjectName('chat_item')

        self.label = qfluentwidgets.BodyLabel(self.chat_model.label.value)

        self.more_button = qfluentwidgets.TransparentToolButton(FluentIcon.MORE, self)
        self.more_button.setFixedSize(18, 18)
        self.more_button.clicked.connect(self.more_button_clicked)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.label, 0, QtCore.Qt.AlignLeft)
        layout.addSpacerItem(QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        ))
        layout.addWidget(self.more_button, 0, QtCore.Qt.AlignRight)

    def more_button_clicked(self):
        menu = qfluentwidgets.RoundMenu(parent=self)
        edit_action = qfluentwidgets.Action(FluentIcon.EDIT, '编辑', self)
        edit_action.triggered.connect(partial(self.action_triggered, 'edit'))
        menu.addAction(edit_action)

        delete_action = qfluentwidgets.Action(FluentIcon.DELETE, '删除', self)
        delete_action.triggered.connect(partial(self.action_triggered, 'delete'))
        menu.addAction(delete_action)

        x = (self.more_button.width() - menu.width()) // 2 + 10
        pos = self.more_button.mapToGlobal(QtCore.QPoint(x, self.more_button.height()))
        menu.exec(pos)

    def set_active(self):
        self.setStyleSheet('#chat_item {border-left: 4px solid #ffab62ba; border-radius: 6px}')

    def clear_active(self):
        self.setStyleSheet('#chat_item {{border-left: 0 solid transparent}')

    def action_triggered(self, _type):
        if _type == 'edit':
            self.edited.emit()
        else:
            self.deleted.emit()

    def reset_title(self):
        self.label.setText(self.chat_model.label.value)


class ChatListWidget(qfluentwidgets.ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_items = []
        self._chat_client = ChatDB()
        self.current_chat_item = None

        self.setStyleSheet(
            'QScrollArea {border: none; background:transparent}'
        )

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self.scroll_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout(self.scroll_widget)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.main_layout.setContentsMargins(2, 2, 3, 2)
        self.setWidget(self.scroll_widget)

        self.load_items()

    def load_items(self):
        item = None
        for chat in self._chat_client.get_chats():
            model = ChatConfigModel()
            model.from_db(chat, self._chat_client)
            item = self.add_item(model, False)

        if item:
            item.set_active()
            self.current_chat_item = item
            signal_bus.chat_item_clicked.emit(item)

    def add_item(self, chat_model=None, set_active=True):
        if not chat_model:
            chat_model = ChatConfigModel()
            chat_model.save(self._chat_client)

        item = ChatItem(chat_model)
        if set_active:
            item.set_active()
            self.current_chat_item = item

        item.clicked.connect(partial(self.item_clicked, item))
        item.deleted.connect(partial(self.item_deleted, item))
        item.edited.connect(partial(self.item_edited, item))

        self.main_layout.insertWidget(0, item)

        for i in self.chat_items:
            i.clear_active()

        self.chat_items.append(item)
        return item

    def item_clicked(self, item):
        for i in self.chat_items:
            if i != item:
                i.clear_active()
            else:
                i.set_active()

        self.current_chat_item = item
        signal_bus.chat_item_clicked.emit(item)

    def item_deleted(self, item):
        label = item.label.text()
        w = qfluentwidgets.Dialog('删除', f'你确定要删除聊天: {label} ？', self)
        if w.exec():
            self.chat_items.remove(item)
            self._chat_client.delete_chat(item.chat_model.cid.value)

            if self.current_chat_item == item:
                self.current_chat_item = None

            signal_bus.chat_item_deleted.emit()
            item.deleteLater()

            return qfluentwidgets.InfoBar.success(
                '提示', f'聊天: {label} 删除成功！', duration=1500,
                parent=self.parent().parent().parent()
            )

    def item_edited(self, item):
        signal_bus.chat_item_edited.emit(item)
