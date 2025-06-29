from PySide2 import QtCore, QtWidgets
import qtawesome


class TabButton(QtWidgets.QPushButton):
    """自定义标签按钮
    
    特性：
    - 支持可关闭功能
    - 激活/非激活状态切换
    - 动态样式更新
    - 关闭按钮位置自适应
    - 拖拽排序功能
    """
    close_requested = QtCore.Signal(object)  # 关闭信号
    rename_requested = QtCore.Signal(object, str)  # 重命名信号 (tab_button, new_name)
    drag_started = QtCore.Signal(object)  # 拖拽开始信号
    drag_moved = QtCore.Signal(object, QtCore.QPoint)  # 拖拽移动信号
    drag_finished = QtCore.Signal(object, QtCore.QPoint)  # 拖拽结束信号

    def __init__(self, text, closable=True, parent=None):
        super().__init__(text, parent)
        self.closable = closable
        self.is_active = False
        self.setObjectName('tab_button')
        
        # 拖拽相关变量
        self.drag_start_position = QtCore.QPoint()
        self.is_dragging = False
        self.drag_threshold = 5  # 拖拽阈值

        # 设置基本样式
        self.setCheckable(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.setFixedHeight(30)
        self.setMinimumWidth(80)
        self.setMaximumWidth(200)

        # 如果可关闭，创建关闭按钮
        if self.closable:
            self.close_btn = QtWidgets.QPushButton("×", self)
            self.close_btn.setFixedSize(16, 16)
            self.close_btn.setCursor(QtCore.Qt.PointingHandCursor)
            self.close_btn.clicked.connect(lambda: self.close_requested.emit(self))
            self.close_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: #666;
                    font-weight: bold;
                    border-radius: 6px;
                    font-size: 12px;
                    margin-left: 6px;
                    cursor: pointer;
                }
                QPushButton:hover {
                    color: #ff4444;
                    
                }
            """)

        self.update_style()

    def set_active(self, active):
        """设置激活状态"""
        self.is_active = active
        self.setChecked(active)
        self.update_style()

    def update_style(self):
        """更新样式 - 核心样式算法"""
        base_style = """
            #tab_button {
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 5px 15px;
                font-size: 14px;
            }
        """
        
        if self.is_dragging:
            # 拖拽时的样式
            drag_style = """
                #tab_button {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    opacity: 0.8;
                    font-weight: bold;
                    color: #1976d2;
                }
            """
            self.setStyleSheet(base_style + drag_style)
        elif self.is_active:
            # 激活状态样式
            active_style = """
                #tab_button {
                    background-color: #ffffff;
                    border: 1px solid #fff;
                    font-weight: bold;
                    color: #222;
                }
            """
            self.setStyleSheet(base_style + active_style)
        else:
            # 普通状态样式
            normal_style = """
                #tab_button {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-bottom: none;
                    color: #888;
                }
                #tab_button:hover {
                    background-color: #e8e8e8;
                }
            """
            self.setStyleSheet(base_style + normal_style)

    def mousePressEvent(self, event):
        """鼠标按下事件 - 拖拽检测起点"""
        if event.button() == QtCore.Qt.LeftButton:
            # 检查是否点击在关闭按钮上
            if self.closable and hasattr(self, 'close_btn'):
                close_btn_rect = self.close_btn.geometry()
                if close_btn_rect.contains(event.pos()):
                    # 点击在关闭按钮上，不启动拖拽
                    super().mousePressEvent(event)
                    return
            
            # 记录拖拽起点和全局鼠标位置
            self.drag_start_position = event.pos()
            # 记录全局鼠标位置用于拖拽偏移计算
            QtWidgets.QApplication.instance().setProperty("lastMousePos", self.mapToGlobal(event.pos()))
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽检测和处理"""
        if not (event.buttons() & QtCore.Qt.LeftButton):
            return

        # 检查是否超过拖拽阈值
        if not self.is_dragging:
            distance = (event.pos() - self.drag_start_position).manhattanLength()
            if distance >= self.drag_threshold:
                # 开始拖拽
                self.is_dragging = True
                self.update_style()
                self.drag_started.emit(self)
        
        if self.is_dragging:
            # 发射拖拽移动信号
            global_pos = self.mapToGlobal(event.pos())
            self.drag_moved.emit(self, global_pos)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 拖拽结束处理"""
        if self.is_dragging and event.button() == QtCore.Qt.LeftButton:
            # 结束拖拽
            self.is_dragging = False
            self.update_style()
            
            # 发射拖拽结束信号
            global_pos = self.mapToGlobal(event.pos())
            self.drag_finished.emit(self, global_pos)
        elif self.is_dragging:
            # 拖拽被取消，恢复状态
            self.is_dragging = False
            self.update_style()
        
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """处理双击事件 - 重命名功能"""
        if event.button() == QtCore.Qt.LeftButton and not self.is_dragging:
            self.rename_requested.emit(self, self.text())
        
        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event):
        """调整关闭按钮位置 - 自适应位置算法"""
        super().resizeEvent(event)
        if self.closable and hasattr(self, 'close_btn'):
            # 将关闭按钮放在右上角
            self.close_btn.move(self.width() - 20, 4)


class CustomTabBar(QtWidgets.QWidget):
    """自定义标签栏
    
    特性：
    - 水平滚动支持
    - 鼠标滚轮切换标签
    - 添加新标签功能
    - 标签可见性确保算法
    - 拖拽排序功能
    """
    tab_changed = QtCore.Signal(int)  # 标签页切换信号
    tab_close_requested = QtCore.Signal(int)  # 标签页关闭信号
    add_tab_requested = QtCore.Signal()  # 添加标签页信号
    tab_rename_requested = QtCore.Signal(int, str)  # 标签页重命名信号 (index, new_name)
    tab_moved = QtCore.Signal(int, int)  # 标签页移动信号 (from_index, to_index)
    tab_dragged = QtCore.Signal(int, int)  # 标签页拖拽信号 (from_index, to_index)

    def __init__(self, show_add_button=True, parent=None):
        super().__init__(parent)
        self.tab_buttons = []
        self.current_index = 0
        self.scroll_offset = 0  # 滚动偏移量
        self.show_add_button = show_add_button
        
        # 拖拽相关变量
        self.dragging_tab = None  # 当前拖拽的标签页
        self.drop_indicator = None  # 拖拽插入指示器
        self.drag_insert_index = -1  # 插入位置索引
        self.drag_preview = None  # 拖拽预览标签页
        self.drag_offset = QtCore.QPoint()  # 拖拽偏移量

        # 创建水平布局
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(2, 0, 0, 0)
        self.layout.setSpacing(2)

        # 创建滚动区域（隐藏滚动条）
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(32)
        self.scroll_area.setStyleSheet('border: none; margin: 0px; padding: 0px;')

        # 创建标签容器
        self.tab_container = QtWidgets.QWidget()
        self.tab_layout = QtWidgets.QHBoxLayout(self.tab_container)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(1)

        # 添加伸缩空间
        self.tab_layout.addStretch()

        # 创建拖拽插入指示器
        self.create_drop_indicator()

        # 创建添加按钮（可选）
        if self.show_add_button:
            self.add_button = QtWidgets.QPushButton('')
            self.add_button.setIcon(qtawesome.icon('fa.plus', color='#555'))
            self.add_button.setFixedSize(30, 30)
            self.add_button.setToolTip("添加新标签页")
            self.add_button.setCursor(QtCore.Qt.PointingHandCursor)
            self.add_button.clicked.connect(self.add_tab_requested.emit)

        # 设置滚动区域
        self.scroll_area.setWidget(self.tab_container)

        # 添加到主布局
        self.layout.addWidget(self.scroll_area)
        if self.show_add_button:
            self.layout.addWidget(self.add_button)

        # 启用鼠标滚轮事件
        self.setMouseTracking(True)

    def create_drop_indicator(self):
        """创建拖拽插入指示器"""
        self.drop_indicator = QtWidgets.QLabel(self.tab_container)
        self.drop_indicator.setFixedSize(3, 28)
        self.drop_indicator.setStyleSheet("""
            QLabel {
                background-color: #2196f3;
                border-radius: 1px;
                margin: 1px 0px;
            }
        """)
        self.drop_indicator.hide()

    def create_drag_preview(self, tab_button):
        """创建拖拽预览"""
        if self.drag_preview:
            self.destroy_drag_preview()
            
        # 创建预览标签页（顶层窗口）
        self.drag_preview = QtWidgets.QLabel()
        self.drag_preview.setWindowFlags(
            QtCore.Qt.Tool | 
            QtCore.Qt.FramelessWindowHint | 
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.X11BypassWindowManagerHint
        )
        
        # 设置预览内容和样式
        self.drag_preview.setText(tab_button.text())
        self.drag_preview.setFixedSize(tab_button.size())
        
        # 复制原标签页的样式，但添加拖拽效果
        preview_style = """
            QLabel {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 5px 15px;
                font-size: 14px;
                font-weight: bold;
                color: #1976d2;
                opacity: 0.9;
            }
        """
        self.drag_preview.setStyleSheet(preview_style)
        self.drag_preview.setAlignment(QtCore.Qt.AlignCenter)
        
        # 计算拖拽偏移量（鼠标相对于标签页左上角的位置）
        last_mouse_pos = QtWidgets.QApplication.instance().property("lastMousePos")
        if last_mouse_pos and not last_mouse_pos.isNull():
            mouse_pos = tab_button.mapFromGlobal(last_mouse_pos)
            self.drag_offset = mouse_pos
        else:
            # 如果没有记录的鼠标位置，使用标签页中心作为偏移
            self.drag_offset = QtCore.QPoint(tab_button.width() // 2, tab_button.height() // 2)
        
        # 初始位置
        global_pos = tab_button.mapToGlobal(QtCore.QPoint(0, 0))
        initial_pos = global_pos - self.drag_offset
        self.drag_preview.move(initial_pos)
        
        # 显示预览
        self.drag_preview.show()
        self.drag_preview.raise_()

    def destroy_drag_preview(self):
        """销毁拖拽预览"""
        if self.drag_preview:
            self.drag_preview.hide()
            self.drag_preview.deleteLater()
            self.drag_preview = None

    def add_tab(self, text, closable=True):
        """添加标签页 - 核心添加算法"""
        tab_button = TabButton(text, closable)
        tab_button.clicked.connect(lambda: self.on_tab_clicked(tab_button))
        tab_button.close_requested.connect(self.on_tab_close_requested)
        tab_button.rename_requested.connect(self.on_tab_rename_requested)
        
        # 连接拖拽信号
        tab_button.drag_started.connect(self.on_drag_started)
        tab_button.drag_moved.connect(self.on_drag_moved)
        tab_button.drag_finished.connect(self.on_drag_finished)

        # 插入到伸缩空间之前
        self.tab_layout.insertWidget(len(self.tab_buttons), tab_button)
        self.tab_buttons.append(tab_button)

        # 如果是第一个标签页，设为激活状态
        if len(self.tab_buttons) == 1:
            self.set_current_index(0)

        # 确保新添加的标签页可见
        self.ensure_tab_visible(len(self.tab_buttons) - 1)

        return len(self.tab_buttons) - 1

    def remove_tab(self, index):
        """移除标签页 - 核心移除算法"""
        if 0 <= index < len(self.tab_buttons):
            tab_button = self.tab_buttons.pop(index)
            self.tab_layout.removeWidget(tab_button)
            tab_button.deleteLater()

            # 调整当前索引 - 智能索引调整算法
            if index <= self.current_index and self.current_index > 0:
                self.current_index -= 1
            elif self.current_index >= len(self.tab_buttons) and len(self.tab_buttons) > 0:
                self.current_index = len(self.tab_buttons) - 1

            # 更新显示
            if len(self.tab_buttons) > 0:
                self.set_current_index(self.current_index)

    def set_current_index(self, index):
        """设置当前激活的标签页 - 核心激活算法"""
        if 0 <= index < len(self.tab_buttons):
            # 取消所有标签页的激活状态
            for i, tab_button in enumerate(self.tab_buttons):
                tab_button.set_active(i == index)

            self.current_index = index
            # 确保当前标签页可见
            self.ensure_tab_visible(index)
            self.tab_changed.emit(index)

    def get_current_index(self):
        """获取当前激活的标签页索引"""
        return self.current_index

    def count(self):
        """获取标签页数量"""
        return len(self.tab_buttons)

    def tab_text(self, index):
        """获取标签页文本"""
        if 0 <= index < len(self.tab_buttons):
            return self.tab_buttons[index].text()
        return ""

    def set_tab_text(self, index, text):
        """设置标签页文本"""
        if 0 <= index < len(self.tab_buttons):
            self.tab_buttons[index].setText(text)

    def on_tab_clicked(self, tab_button):
        """处理标签页点击"""
        index = self.tab_buttons.index(tab_button)
        self.set_current_index(index)

    def on_tab_close_requested(self, tab_button):
        """处理标签页关闭请求"""
        index = self.tab_buttons.index(tab_button)
        self.tab_close_requested.emit(index)

    def on_tab_rename_requested(self, tab_button, old_name):
        index = self.tab_buttons.index(tab_button)
        self.tab_rename_requested.emit(index, old_name)

    def on_drag_started(self, tab_button):
        """处理拖拽开始"""
        self.dragging_tab = tab_button
        
        # 创建拖拽预览
        self.create_drag_preview(tab_button)
        
        # 设置原标签页为半透明
        tab_button.setStyleSheet(tab_button.styleSheet() + """
            #tab_button {
                opacity: 0.3;
            }
        """)
        
        print(f"开始拖拽标签页: {tab_button.text()}")

    def on_drag_moved(self, tab_button, global_pos):
        """处理拖拽移动"""
        if self.dragging_tab != tab_button:
            return
            
        # 更新拖拽预览位置
        if self.drag_preview:
            preview_pos = global_pos - self.drag_offset
            self.drag_preview.move(preview_pos)
            
        # 将全局坐标转换为标签容器的本地坐标
        local_pos = self.tab_container.mapFromGlobal(global_pos)
        
        # 计算插入位置
        insert_index = self.calculate_drop_position(local_pos.x())
        
        # 更新插入指示器位置
        self.update_drop_indicator(insert_index)

    def on_drag_finished(self, tab_button, global_pos):
        """处理拖拽结束"""
        if self.dragging_tab != tab_button:
            return
            
        # 这些清理工作将在cleanup_drag_state中完成
        
        # 获取源索引和目标索引
        from_index = self.tab_buttons.index(tab_button)
        
        # 将全局坐标转换为标签容器的本地坐标
        local_pos = self.tab_container.mapFromGlobal(global_pos)
        to_index = self.calculate_drop_position(local_pos.x())
        
        # 调整目标索引（如果目标位置在源位置之后，需要减1）
        if to_index > from_index:
            to_index -= 1
            
        # 执行移动
        if 0 <= to_index < len(self.tab_buttons) and from_index != to_index:
            self.move_tab(from_index, to_index)
            
        # 清理拖拽状态
        self.cleanup_drag_state()
        self.tab_dragged.emit(from_index, to_index)
        print(f"拖拽结束: {tab_button.text()} 从 {from_index} 移动到 {to_index}")

    def cleanup_drag_state(self):
        """清理拖拽状态"""
        if self.dragging_tab:
            # 恢复拖拽标签页的样式
            self.dragging_tab.update_style()
            
        # 销毁拖拽预览
        self.destroy_drag_preview()
        
        # 隐藏插入指示器
        self.drop_indicator.hide()
        
        # 重置状态变量
        self.dragging_tab = None
        self.drag_insert_index = -1

    def calculate_drop_position(self, x):
        """计算拖拽插入位置"""
        if not self.tab_buttons:
            return 0
            
        # 检查是否在第一个标签页之前
        first_tab = self.tab_buttons[0]
        if x < first_tab.x():
            return 0
            
        # 检查每个标签页的中点
        for i, tab_button in enumerate(self.tab_buttons):
            tab_center = tab_button.x() + tab_button.width() // 2
            if x < tab_center:
                return i
                
        # 如果超过所有标签页，插入到末尾
        return len(self.tab_buttons)

    def update_drop_indicator(self, insert_index):
        """更新拖拽插入指示器位置"""
        if insert_index == self.drag_insert_index:
            return
            
        self.drag_insert_index = insert_index
        
        if insert_index < 0 or insert_index > len(self.tab_buttons):
            self.drop_indicator.hide()
            return
            
        # 计算指示器位置
        if insert_index == 0:
            # 插入到开头
            if self.tab_buttons:
                x = self.tab_buttons[0].x() - 2
            else:
                x = 0
        elif insert_index >= len(self.tab_buttons):
            # 插入到末尾
            last_tab = self.tab_buttons[-1]
            x = last_tab.x() + last_tab.width() + 1
        else:
            # 插入到中间
            prev_tab = self.tab_buttons[insert_index - 1]
            next_tab = self.tab_buttons[insert_index]
            x = (prev_tab.x() + prev_tab.width() + next_tab.x()) // 2 - 1
            
        # 设置指示器位置并显示
        self.drop_indicator.move(x, 2)
        self.drop_indicator.show()

    def move_tab(self, from_index, to_index):
        """移动标签页位置"""
        if from_index == to_index or from_index < 0 or to_index < 0:
            return
            
        if from_index >= len(self.tab_buttons) or to_index >= len(self.tab_buttons):
            return
            
        # 移动标签页按钮
        tab_button = self.tab_buttons.pop(from_index)
        self.tab_buttons.insert(to_index, tab_button)
        
        # 重新排列布局
        # 先移除所有标签页
        for tab in self.tab_buttons:
            self.tab_layout.removeWidget(tab)
            
        # 按新顺序重新添加
        for i, tab in enumerate(self.tab_buttons):
            self.tab_layout.insertWidget(i, tab)
            
        # 调整当前索引
        if from_index == self.current_index:
            # 当前活动标签页被移动
            self.current_index = to_index
        elif from_index < self.current_index <= to_index:
            # 当前活动标签页的索引需要减1
            self.current_index -= 1
        elif to_index <= self.current_index < from_index:
            # 当前活动标签页的索引需要加1
            self.current_index += 1
            
        # 更新激活状态显示
        self.set_current_index(self.current_index)
        
        # 发射移动信号
        self.tab_moved.emit(from_index, to_index)

    def ensure_tab_visible(self, index):
        """确保指定的标签页在可见区域内 - 可见性确保算法"""
        if 0 <= index < len(self.tab_buttons):
            tab_button = self.tab_buttons[index]
            # 滚动到标签页位置
            self.scroll_area.ensureWidgetVisible(tab_button, 50, 0)

    def wheelEvent(self, event):
        """处理滚轮事件 - 智能滚轮响应算法"""
        # 检查是否需要滚动（标签页总宽度超过可见区域）
        if self.tab_container.sizeHint().width() > self.scroll_area.width():
            # 水平滚动标签栏
            scroll_bar = self.scroll_area.horizontalScrollBar()
            if event.angleDelta().y() > 0:
                # 向上滚动，向左滚动标签栏
                scroll_bar.setValue(scroll_bar.value() - 50)
            else:
                # 向下滚动，向右滚动标签栏
                scroll_bar.setValue(scroll_bar.value() + 50)
        else:
            # 如果不需要滚动，则切换标签页
            if event.angleDelta().y() > 0:
                # 向上滚动，切换到前一个标签页
                if self.current_index > 0:
                    self.set_current_index(self.current_index - 1)
            else:
                # 向下滚动，切换到后一个标签页
                if self.current_index < len(self.tab_buttons) - 1:
                    self.set_current_index(self.current_index + 1)
