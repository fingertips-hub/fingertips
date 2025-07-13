from urllib.parse import urljoin, urlparse
import os

from PySide2 import QtWidgets, QtCore, QtGui
import requests
import qtawesome
from bs4 import BeautifulSoup

from fingertips.utils import get_exe_path
from fingertips.sidebar_widgets.software_card.widgets import ConfirmDialog

request_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


class SoftwareItemWidget(QtWidgets.QWidget):
    """自定义软件项小部件"""
    item_renamed = QtCore.Signal()

    def __init__(self, icon, name, parent=None):
        super().__init__(parent)
        self._original_name = name
        self._edit_mode = False
        self._init_ui(icon, name)

    def _init_ui(self, icon, name):
        self.setMaximumSize(80, 80)

        self.name_label = QtWidgets.QLabel(name)
        self.name_label.setFixedHeight(28)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet('margin: 0 2px;')

        # 创建编辑器（初始时隐藏）
        self.name_editor = QtWidgets.QLineEdit(name)
        self.name_editor.setFixedHeight(28)
        self.name_editor.setAlignment(QtCore.Qt.AlignCenter)
        self.name_editor.setStyleSheet('margin: 0 2px; border: 1px solid #007ACC; border-radius: 2px;')
        self.name_editor.hide()
        
        # 连接编辑器事件
        self.name_editor.returnPressed.connect(self._finish_edit)
        self.name_editor.editingFinished.connect(self._on_editing_finished)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        self.icon_label.setFixedSize(40, 40)
        pixmap = icon.pixmap(40, 40).scaled(
            40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.icon_label.setPixmap(pixmap)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(2)
        layout.addWidget(self.icon_label, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_editor, alignment=QtCore.Qt.AlignCenter)

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == QtCore.Qt.RightButton and not self._edit_mode:
            self._start_edit()
        super().mousePressEvent(event)

    def _start_edit(self):
        """开始编辑模式"""
        if self._edit_mode:
            return
            
        self._edit_mode = True
        self.name_label.hide()
        self.name_editor.setText(self.name_label.text())
        self.name_editor.show()
        self.name_editor.setFocus()
        self.name_editor.selectAll()

    def _finish_edit(self):
        """完成编辑"""
        if not self._edit_mode:
            return
            
        new_name = self.name_editor.text().strip()
        if new_name:
            self.name_label.setText(new_name)
        
        self._edit_mode = False
        self.name_editor.hide()
        self.name_label.show()
        if new_name != self._original_name:
            self.item_renamed.emit()

    def _on_editing_finished(self):
        """编辑完成时调用（失去焦点时）"""
        # 使用 QTimer 延迟执行，避免与其他事件冲突
        QtCore.QTimer.singleShot(50, self._finish_edit)

    def get_display_name(self):
        """获取当前显示的名称"""
        return self.name_label.text()

    def set_display_name(self, name):
        """设置显示名称"""
        self.name_label.setText(name)
        if not self._edit_mode:
            self.name_editor.setText(name)


class SoftwareListWidget(QtWidgets.QListWidget):
    """自定义软件列表小部件"""
    item_added = QtCore.Signal()
    item_removed = QtCore.Signal()
    item_renamed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(2)
        self.setStyleSheet('''
            QListWidget {
                border: none;
                background-color: transparent;
            }
            
            /* 垂直滚动条样式 */
            QScrollBar:vertical {
                background-color: rgba(240, 240, 240, 0.3);
                width: 8px;
                border: none;
                border-radius: 4px;
                margin: 0px;
            }
            
            /* 滚动条滑块 */
            QScrollBar::handle:vertical {
                background-color: rgba(160, 160, 160, 0.8);
                min-height: 20px;
                border-radius: 4px;
                margin: 0px;
            }
            
            /* 滚动条滑块悬停效果 */
            QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 122, 204, 0.8);
            }
            
            /* 滚动条滑块按下效果 */
            QScrollBar::handle:vertical:pressed {
                background-color: rgba(0, 122, 204, 1.0);
            }
            
            /* 隐藏滚动条上下箭头 */
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
                background: none;
                border: none;
            }
            
            /* 隐藏滚动条页面区域 */
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        ''')

        self.setAcceptDrops(True)

    @staticmethod
    def _get_website_info(url):
        try:
            response = requests.get(url, headers=request_headers, timeout=3)
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # 获取网站标题
            title = soup.find('title')
            website_name = title.get_text().strip() if title else "未找到标题"

            # 查找favicon
            favicon_url = ''

            # 方法1: 查找link标签中的icon
            icon_links = soup.find_all('link', rel=lambda x: x and (
                        'icon' in x.lower() or 'shortcut' in x.lower()))
            if icon_links:
                favicon_url = urljoin(url, icon_links[0].get('href'))
            else:
                # 方法2: 尝试默认的favicon.ico路径
                parsed_url = urlparse(url)
                default_favicon = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
                try:
                    favicon_response = requests.head(default_favicon, timeout=3)
                    if favicon_response.status_code == 200:
                        favicon_url = default_favicon
                except:
                    pass

            return {
                'name': website_name,
                'favicon_url': favicon_url,
                'url': url
            }

        except Exception as e:
            return {
                'name': '未知网站',
                'favicon_url': '',
                'url': url
            }

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            for url in event.mimeData().urls():
                source_file = url.toLocalFile()
                if not source_file:
                    http_url = url.toString()
                    web_info = self._get_website_info(http_url)
                    self.add_item(
                        web_info['name'],
                        web_info['favicon_url'],
                        web_info['url'],
                        _type='website'
                    )
                else:
                    file_path = get_exe_path(source_file)
                    name = (
                        source_file.split('/')[-1].split('.')[0]
                        if source_file.lower().endswith(('.lnk', '.exe')) else
                        source_file.split('/')[-1]
                    )
                    self.add_item(name, file_path, source_file)
                self.item_added.emit()
        else:
            event.setDropAction(QtCore.Qt.MoveAction)
            super().dropEvent(event)

    @staticmethod
    def _load_icon_from_http(url):
        if not url:
            return qtawesome.icon('msc.browser')

        try:
            response = requests.get(url, headers=request_headers, timeout=3)
            response.raise_for_status()

            # 将下载的数据转换为QByteArray
            data = QtCore.QByteArray(response.content)

            # 从数据创建QPixmap
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)

            # 创建QIcon
            return QtGui.QIcon(pixmap)

        except requests.RequestException as e:
            print(f"下载图标失败: {e}")
            return qtawesome.icon('fa5s.browser')

    def add_item(self, name, file_path, link_path=None, _type='file'):
        if _type == 'website':
            icon = self._load_icon_from_http(file_path)
        else:
            icon = QtWidgets.QFileIconProvider().icon(
                QtCore.QFileInfo(file_path))
        item_widget = SoftwareItemWidget(icon, name)

        item = QtWidgets.QListWidgetItem(self)
        item.setSizeHint(QtCore.QSize(80, 80))
        item.path = link_path or file_path
        item.type = _type
        item.icon = file_path
        # 连接信号
        item_widget.item_renamed.connect(self.item_renamed.emit)

        self.setItemWidget(item, item_widget)
        self.addItem(item)
        return item

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            selected_items = self.selectedItems()

            if not selected_items:
                return

            if not ConfirmDialog.show_confirm('删除软件', '您确定要删除选中的软件吗？'):
                return

            for item in selected_items:
                self.takeItem(self.row(item))
            self.item_removed.emit()

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            if item.type == 'website':
                import webbrowser
                webbrowser.open(item.path)
            else:
                import os
                os.startfile(item.path)

    def get_all_items_info(self):
        """获取所有项目的信息，返回便于序列化的数据结构
        
        Returns:
            list: 包含所有项目信息的列表，每个项目是一个字典，包含：
                - name: 显示名称
                - path: 文件路径或网址
                - type: 类型（'file' 或 'website'）
                - original_path: 原始路径（对于快捷方式等）
        """
        items_info = []
        
        for i in range(self.count()):
            item = self.item(i)
            item_widget = self.itemWidget(item)
            
            if item and item_widget:
                # 获取显示名称
                display_name = item_widget.get_display_name()
                
                # 构建项目信息字典
                item_info = {
                    'name': display_name,
                    'path': getattr(item, 'path', ''),
                    'type': getattr(item, 'type', 'file'),
                    'icon': getattr(item, 'icon', ''),
                }

                items_info.append(item_info)
        
        return items_info

    def load_items_from_info(self, items_info):
        """从序列化的信息中加载项目
        
        Args:
            items_info (list): 项目信息列表，格式与 get_all_items_info() 返回值相同
        """
        # 清空现有项目
        self.clear()
        
        # 添加项目
        for item_info in items_info:
            name = item_info.get('name', '未知项目')
            path = item_info.get('path', '')
            item_type = item_info.get('type', 'file')
            icon = item_info.get('icon', '')
            
            if not path:
                continue
                
            try:
                if item_type == 'website':
                    # 对于网站，path 就是 favicon_url，需要单独处理
                    # 这里简化处理，直接使用默认图标
                    self.add_item(name, icon, path, _type='website')
                else:
                    # 对于文件，检查文件是否存在
                    if os.path.exists(path):
                        self.add_item(name, path, path, _type='file')
                    else:
                        # 文件不存在时，仍然添加但使用默认图标
                        self.add_item(name, path, path, _type='file')
                        
            except Exception as e:
                print(f"加载项目失败: {name}, 错误: {e}")
                continue


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = SoftwareListWidget()
    widget.show()
    app.exec_()
