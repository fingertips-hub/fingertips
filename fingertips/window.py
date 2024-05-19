import os

from PySide2 import QtWidgets
from PySide2 import QtCore

from fingertips.widgets import SoftwareListWidget, InputLineEdit, AskAIWidget
from fingertips.hotkey import HotkeyThread
from fingertips.core.thread import AskAIThread
from fingertips.core.plugin import PluginRegister
from fingertips.core.action import ActionRegister
from fingertips.utils import get_logger, get_select_entity
from fingertips.action_menu import ActionMenu, AIResultWindow
from fingertips.settings.config_model import config_model

log = get_logger('Fingertips')


class Fingertips(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.placeholder = 'Hello, Fingertips!'
        self.RESULT_ITEM_HEIGHT = 62
        self.ai_view = None

        self.init_ui()

        self.plugin_register = PluginRegister(self)
        self.action_register = ActionRegister(self)

        self.init_hotkey()

    def set_position(self):
        pos = QtWidgets.QDesktopWidget().availableGeometry().center()
        pos.setX(pos.x() - (self.width() / 2))
        pos.setY(pos.y() - (pos.y() / 2))
        self.move(pos)

    def init_ui(self):
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        self.setFixedSize(QtCore.QSize(830, 380))

        self.load_style()
        self.installEventFilter(self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        inner_widget = QtWidgets.QWidget()
        inner_widget.setObjectName('inner_widget')
        inner_layout = QtWidgets.QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.setSpacing(2)

        self.input_line_edit = InputLineEdit()
        self.input_line_edit.setPlaceholderText(self.placeholder)
        self.input_line_edit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.input_line_edit.setMinimumHeight(66)
        self.input_line_edit.returnPressed.connect(
            self.input_line_edit_return_pressed)
        self.input_line_edit.textChanged.connect(
            self.input_line_edit_text_changed)

        self.result_list_widget = QtWidgets.QListWidget()
        self.result_list_widget.setObjectName('result_list_widget')
        self.result_list_widget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.result_list_widget.keyPressEvent = self.result_list_key_press_event
        self.result_list_widget.itemClicked.connect(self.execute_result_item)

        self.software_list_widget = SoftwareListWidget()
        self.software_list_widget.setObjectName('software_list_widget')
        self.software_list_widget.item_double_clicked.connect(
            self.software_list_widget_item_double_clicked)

        self.ask_viewer = AskAIWidget()
        self.ask_viewer.setObjectName('ask_viewer')
        self._set_ask_viewer_status(False)
        self._set_result_list_widget_status(False)

        inner_layout.addWidget(self.input_line_edit)
        inner_layout.addWidget(self.software_list_widget)
        inner_layout.addWidget(self.ask_viewer)

        inner_layout.addWidget(self.result_list_widget)

        layout.addWidget(inner_widget)

        self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)

    def result_list_key_press_event(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            return self.execute_result_item(
                self.result_list_widget.currentItem())
        if event.key() == QtCore.Qt.Key_Backspace:
            self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)
            self.result_list_widget.setCurrentRow(-1)
            self.input_line_edit.setText(self.input_line_edit.text()[:-1])
            return

        super(QtWidgets.QListWidget, self.result_list_widget).keyPressEvent(
            event)

    def execute_result_item(self, item):
        result_item = self.result_list_widget.itemWidget(item)
        if not result_item:
            return

        input_text = self.input_line_edit.text().strip()
        if result_item.keyword and (
                input_text == result_item.keyword or
                not input_text.startswith(result_item.keyword)):
            self.input_line_edit.setText(result_item.keyword + ' ')
            self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)
            self.result_list_widget.setCurrentRow(-1)
        else:
            self.input_line_edit_return_pressed()

    def _ask_viewer_scroll_to_bottom(self):
        scrollbar = self.ask_viewer.verticalScrollBar()
        # 检查是否已经滚动到底部
        if scrollbar.value() != scrollbar.maximum():
            QtCore.QTimer.singleShot(
                100,
                lambda: scrollbar.setValue(scrollbar.maximum())
            )

    def init_hotkey(self):
        global_shortcuts = {
            config_model.main_window_shortcut.value: '',
            config_model.action_menu_shortcut.value: 'show_menus',
            config_model.ai_resend_shortcut.value: 'ai_resend',
        }
        plugin_shortcuts = self.plugin_register.get_keyword_by_shortcut()
        if set(global_shortcuts) & set(plugin_shortcuts):
            log.error('There are duplicate shortcuts.')
            log.error(u'global_shortcuts: {}'.format(global_shortcuts))
            log.error(u'plugin_shortcuts: {}'.format(plugin_shortcuts))
            raise ValueError('There are duplicate shortcuts.')

        global_shortcuts.update(self.plugin_register.get_keyword_by_shortcut())

        hotkeys = HotkeyThread(global_shortcuts, self)
        hotkeys.show_main_sign.connect(self.set_visible)
        hotkeys.shortcut_triggered.connect(self.shortcut_triggered)
        hotkeys.start()

    def software_list_widget_item_double_clicked(self, exe_path):
        os.startfile(exe_path)
        self.set_visible()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.set_visible()

        return super().keyPressEvent(event)

    def shortcut_triggered(self, plugin_name):
        if self.plugin_register.get_plugin(plugin_name):
            self.set_show()
            self.input_line_edit.setText(plugin_name + ' ')

        global_shortcuts = {
            config_model.main_window_shortcut.value: '',
            config_model.action_menu_shortcut.value: 'show_menus',
            config_model.ai_resend_shortcut.value: 'ai_resend'
        }
        if plugin_name in global_shortcuts.values():
            getattr(self, plugin_name)()

    def show_menus(self):
        data = get_select_entity()
        log.info(u'已调用quicker menus，{}'.format(data))

        rm = ActionMenu()
        rm.triggered.connect(self.action_menu_triggered)
        rm.show_menu(data)

    def ai_resend(self):
        if self.ai_view is None:
            return

        self.ai_view.resend_button_clicked()

    def action_menu_triggered(self, data):
        if data['select']['type'] == 'text':
            self.ai_view = AIResultWindow(data)
            self.ai_view.closed.connect(self.ai_view_closed)
            self.ai_view.request()
            self.ai_view.show()

    def ai_view_closed(self):
        self.ai_view = None

    def load_style(self):
        with open('res/theme.css') as f:
            self.setStyleSheet(f.read())

    def _set_result(self, text):
        self.ask_viewer.set_html(text)

    def input_line_edit_return_pressed(self):
        text = self.input_line_edit.text().strip()
        if not text:
            return

        if text.startswith('/'):
            if self.result_list_widget.count() < 1:
                return
            if len(text.split(' ', 1)) == 2:
                plugin_keyword, execute_str = text.strip().split(' ', 1)
                plugin_keyword = plugin_keyword[1:]
            else:
                plugin_keyword = next(iter(
                    self.result_list_widget.itemWidget(
                        self.result_list_widget.item(i)).keyword
                    for i in range(self.result_list_widget.count()) if
                    self.result_list_widget.itemWidget(
                        self.result_list_widget.item(i)).keyword == text[1:]
                ), '')
                execute_str = ''

            if not plugin_keyword:
                return

            result_item = None
            if self.result_list_widget.selectedItems():
                result_item = self.result_list_widget.itemWidget(
                    self.result_list_widget.currentItem())
            elif self.result_list_widget.count() == 1:
                result_item = self.result_list_widget.itemWidget(
                    self.result_list_widget.item(0))
            result_items = self.plugin_register.execute(
                plugin_keyword, execute_str, result_item,
                self.plugin_register.plugins()
            )

            if not result_items:
                self.input_line_edit.clear()
                self.close()
            else:
                self.add_items(result_items)

            return

        self._set_software_list_widget_status(False)
        self._set_result_list_widget_status(False)
        self._set_ask_viewer_status(True)
        self.ask_viewer.show_loading()

        ask_ai_thread = AskAIThread(text, parent=self)
        ask_ai_thread.resulted.connect(self._set_result)
        ask_ai_thread.finished.connect(self.ask_ai_thread_finished)
        ask_ai_thread.start()

    def ask_ai_thread_finished(self, text):
        self.ask_viewer.source_text = text
        self.ask_viewer.hide_loading()

    def _set_ask_viewer_status(self, is_show=False):
        if is_show:
            self.ask_viewer.show()
            self.ask_viewer.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred,
                QtWidgets.QSizePolicy.Preferred
            )
            self.ask_viewer.setFixedSize(820, 300)
            self.ask_viewer.adjustSize()
        else:
            self.ask_viewer.hide()
            self.ask_viewer.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored,
                QtWidgets.QSizePolicy.Ignored
            )

    def _set_software_list_widget_status(self, is_show=False):
        if is_show:
            self.software_list_widget.show()
            self.software_list_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred,
                QtWidgets.QSizePolicy.Preferred
            )
            self.software_list_widget.setFixedSize(820, 300)
            self.software_list_widget.adjustSize()
        else:
            self.software_list_widget.hide()
            self.software_list_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored,
                QtWidgets.QSizePolicy.Ignored
            )

    def _set_result_list_widget_status(self, is_show=False):
        if is_show:
            self.result_list_widget.show()
            self.result_list_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred,
                QtWidgets.QSizePolicy.Preferred
            )
            self.result_list_widget.setFixedSize(820, 300)
            self.result_list_widget.adjustSize()
        else:
            self.result_list_widget.hide()
            self.result_list_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored,
                QtWidgets.QSizePolicy.Ignored
            )

    def input_line_edit_text_changed(self, text):
        if text:
            if not text.startswith('/'):
                return

            self._set_ask_viewer_status(False)
            self._set_software_list_widget_status(False)
            self._set_result_list_widget_status(True)

            if ' ' not in text.strip():
                plugin_keyword = text.strip()[1:]
                result_items = self.plugin_register.search_plugin(
                    plugin_keyword)
            else:
                plugin_keyword, query_str = text.strip().split(' ', 1)
                result_items = self.plugin_register.get_query_result(
                    plugin_keyword[1:], query_str)

            if result_items:
                self.add_items(result_items)
            return

        self._set_result_list_widget_status(False)
        self._set_ask_viewer_status(False)
        self._set_software_list_widget_status(True)

    def add_items(self, result_items):
        self.result_list_widget.clear()

        for item in result_items:
            self.add_item(item)

    def add_item(self, result_item):
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(QtCore.QSize(200, self.RESULT_ITEM_HEIGHT))
        self.result_list_widget.addItem(item)
        self.result_list_widget.setItemWidget(item, result_item)

    def set_show(self):
        self.set_position()
        self.setVisible(True)
        self.activateWindow()
        self.input_line_edit.setFocus(QtCore.Qt.MouseFocusReason)

    def reload_plugin(self):
        self.plugin_register.reload_plugins()

    def set_visible(self):
        if self.isVisible():
            self.input_line_edit.setText('')
            self.software_list_widget.clearSelection()
            self.setVisible(False)
        else:
            self.set_show()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    f = Fingertips()
    f.show()
    app.exec_()
