from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui


class ResizableWidget(QtWidgets.QGraphicsItem):
    """可调整大小的图形项"""

    # 定义调整类型
    RESIZE_NONE = 0
    RESIZE_LEFT = 1
    RESIZE_RIGHT = 2
    RESIZE_TOP = 3
    RESIZE_BOTTOM = 4
    RESIZE_TOP_LEFT = 5
    RESIZE_TOP_RIGHT = 6
    RESIZE_BOTTOM_LEFT = 7
    RESIZE_BOTTOM_RIGHT = 8

    def __init__(self, x, y, width, height, color=QtCore.Qt.lightGray, editable=True): # 新增 editable 参数
        super().__init__()
        self.rect = QtCore.QRectF(0, 0, width, height)
        self.color = color
        self.setPos(x, y)

        self.editable = editable  # 保存编辑状态

        # 根据编辑状态设置初始标志
        flags = QtWidgets.QGraphicsItem.ItemIsFocusable
        if self.editable:
            flags |= QtWidgets.QGraphicsItem.ItemIsSelectable | QtWidgets.QGraphicsItem.ItemIsMovable
        self.setFlags(flags)

        # 调整大小相关
        self.handle_size = 8
        self.edge_width = 6
        self.resize_mode = self.RESIZE_NONE
        self.resize_start_pos = QtCore.QPointF()
        self.resize_start_rect = QtCore.QRectF()
        self.resize_start_item_pos = QtCore.QPointF()
        self.min_size = 50

        self.setAcceptHoverEvents(True)

    def set_editable(self, editable):
        """设置组件是否可编辑"""
        if self.editable == editable:
            return

        self.editable = editable
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, editable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, editable)

        if not editable:
            # 如果变为不可编辑，则取消选择并重置状态
            if self.isSelected():
                self.setSelected(False)
            self.resize_mode = self.RESIZE_NONE
            self.setCursor(QtCore.Qt.ArrowCursor) # 重置光标
        # else:
            # 变为可编辑时，用户需要点击才能选中
            # pass
        self.update() # 请求重绘

    def boundingRect(self):
        return self.rect.adjusted(-self.handle_size, -self.handle_size,
                                  self.handle_size, self.handle_size)

    def paint(self, painter, option, widget):
        painter.fillRect(self.rect, self.color)
        if self.isSelected(): # 仅在选中时绘制边框和手柄
            pen = QtGui.QPen(QtCore.Qt.black, 2)
            painter.setPen(pen)
            painter.drawRect(self.rect)
            self._draw_resize_handles(painter)

    def _draw_resize_handles(self, painter):
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        # 实际绘制手柄的逻辑可以放在这里，或者依赖于 _get_resize_handles 和 paint 的选中状态
        # 例如，遍历 _get_resize_handles() 返回的矩形并绘制它们
        handles = self._get_resize_handles()
        for handle_rect in handles.values():
            painter.drawRect(handle_rect)


    def _get_resize_handles(self):
        hs = self.handle_size
        r = self.rect
        return {
            self.RESIZE_TOP_LEFT: QtCore.QRectF(r.left() - hs / 2, r.top() - hs / 2, hs, hs),
            self.RESIZE_TOP: QtCore.QRectF(r.center().x() - hs / 2, r.top() - hs / 2, hs, hs),
            self.RESIZE_TOP_RIGHT: QtCore.QRectF(r.right() - hs / 2, r.top() - hs / 2, hs, hs),
            self.RESIZE_LEFT: QtCore.QRectF(r.left() - hs / 2, r.center().y() - hs / 2, hs, hs),
            self.RESIZE_RIGHT: QtCore.QRectF(r.right() - hs / 2, r.center().y() - hs / 2, hs, hs),
            self.RESIZE_BOTTOM_LEFT: QtCore.QRectF(r.left() - hs / 2, r.bottom() - hs / 2, hs, hs),
            self.RESIZE_BOTTOM: QtCore.QRectF(r.center().x() - hs / 2, r.bottom() - hs / 2, hs, hs),
            self.RESIZE_BOTTOM_RIGHT: QtCore.QRectF(r.right() - hs / 2, r.bottom() - hs / 2, hs, hs),
        }

    def _get_resize_mode(self, pos):
        if not self.isSelected(): # 如果未选中，则无法调整大小
            return self.RESIZE_NONE

        handles = self._get_resize_handles()
        for mode, handle in handles.items():
            if handle.contains(pos):
                return mode

        ew = self.edge_width
        r = self.rect
        if abs(pos.x() - r.left()) < ew and r.top() < pos.y() < r.bottom(): return self.RESIZE_LEFT
        if abs(pos.x() - r.right()) < ew and r.top() < pos.y() < r.bottom(): return self.RESIZE_RIGHT
        if abs(pos.y() - r.top()) < ew and r.left() < pos.x() < r.right(): return self.RESIZE_TOP
        if abs(pos.y() - r.bottom()) < ew and r.left() < pos.x() < r.right(): return self.RESIZE_BOTTOM
        return self.RESIZE_NONE

    def hoverMoveEvent(self, event):
        if self.editable and self.isSelected():
            current_resize_mode = self._get_resize_mode(event.pos())
            cursor = self._get_cursor_for_resize_mode(current_resize_mode)
            self.setCursor(cursor)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(QtCore.Qt.ArrowCursor)
        super().hoverLeaveEvent(event)

    def _get_cursor_for_resize_mode(self, mode):
        cursors = {
            self.RESIZE_LEFT: QtCore.Qt.SizeHorCursor,
            self.RESIZE_RIGHT: QtCore.Qt.SizeHorCursor,
            self.RESIZE_TOP: QtCore.Qt.SizeVerCursor,
            self.RESIZE_BOTTOM: QtCore.Qt.SizeVerCursor,
            self.RESIZE_TOP_LEFT: QtCore.Qt.SizeFDiagCursor,
            self.RESIZE_TOP_RIGHT: QtCore.Qt.SizeBDiagCursor,
            self.RESIZE_BOTTOM_LEFT: QtCore.Qt.SizeBDiagCursor,
            self.RESIZE_BOTTOM_RIGHT: QtCore.Qt.SizeFDiagCursor,
        }
        return cursors.get(mode, QtCore.Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if not self.editable:
            super().mousePressEvent(event) # 允许焦点等非编辑交互
            return

        # 可编辑时的逻辑
        self.resize_mode = self._get_resize_mode(event.pos()) # 依赖 isSelected()

        if self.resize_mode != self.RESIZE_NONE:
            self.resize_start_pos = event.scenePos()
            self.resize_start_rect = QtCore.QRectF(self.rect)
            self.resize_start_item_pos = self.pos()
            event.accept() # 事件被接受，用于调整大小
        else:
            # 如果不是调整大小，则交给基类处理（例如移动）
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """重写鼠标移动事件，处理边缘区域的拖拽和光标设置"""
        # 如果正在转发拖拽，继续转发到父窗口
        if self._is_forwarding_resize:
            parent = self._get_parent_sidebar()
            if parent:
                # 将ContentView的坐标转换为SuperSidebar的坐标
                parent_pos = self.mapTo(parent, event.pos())
                new_event = QtGui.QMouseEvent(
                    event.type(),
                    parent_pos,
                    event.globalPos(),
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                parent.mouseMoveEvent(new_event)
                return
        
        # 检查是否在调整大小区域
        is_in_resize_area = self._is_in_parent_resize_area(event.pos())
        
        if is_in_resize_area:
            # 如果在父窗口的调整大小区域，强制设置调整大小光标
            self._force_cursor = QtCore.Qt.SizeHorCursor
            self.setCursor(QtCore.Qt.SizeHorCursor)
            # 也在viewport上设置光标
            self.viewport().setCursor(QtCore.Qt.SizeHorCursor)
            # 不调用父类方法，避免光标被覆盖
        else:
            # 不在调整大小区域，停止强制光标并调用父类方法
            self._force_cursor = None
            # 重置view和viewport的光标
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.viewport().setCursor(QtCore.Qt.ArrowCursor)
            super().mouseMoveEvent(event)

    def _perform_resize(self, current_scene_pos):
        delta = current_scene_pos - self.resize_start_pos
        new_rect = QtCore.QRectF(self.resize_start_rect)
        adjust_pos = False
        pos_delta = QtCore.QPointF(0, 0)

        if self.resize_mode == self.RESIZE_LEFT:
            new_width = self.resize_start_rect.width() - delta.x()
            if new_width >= self.min_size:
                new_rect.setWidth(new_width); pos_delta.setX(delta.x()); adjust_pos = True
            else:
                new_rect.setWidth(self.min_size); pos_delta.setX(self.resize_start_rect.width() - self.min_size); adjust_pos = True
        elif self.resize_mode == self.RESIZE_RIGHT:
            new_width = self.resize_start_rect.width() + delta.x()
            new_rect.setWidth(max(new_width, self.min_size))
        elif self.resize_mode == self.RESIZE_TOP:
            new_height = self.resize_start_rect.height() - delta.y()
            if new_height >= self.min_size:
                new_rect.setHeight(new_height); pos_delta.setY(delta.y()); adjust_pos = True
            else:
                new_rect.setHeight(self.min_size); pos_delta.setY(self.resize_start_rect.height() - self.min_size); adjust_pos = True
        elif self.resize_mode == self.RESIZE_BOTTOM:
            new_height = self.resize_start_rect.height() + delta.y()
            new_rect.setHeight(max(new_height, self.min_size))
        elif self.resize_mode == self.RESIZE_TOP_LEFT:
            new_width = self.resize_start_rect.width() - delta.x()
            if new_width >= self.min_size: new_rect.setWidth(new_width); pos_delta.setX(delta.x())
            else: new_rect.setWidth(self.min_size); pos_delta.setX(self.resize_start_rect.width() - self.min_size)
            new_height = self.resize_start_rect.height() - delta.y()
            if new_height >= self.min_size: new_rect.setHeight(new_height); pos_delta.setY(delta.y())
            else: new_rect.setHeight(self.min_size); pos_delta.setY(self.resize_start_rect.height() - self.min_size)
            adjust_pos = True
        elif self.resize_mode == self.RESIZE_TOP_RIGHT:
            new_width = self.resize_start_rect.width() + delta.x()
            new_rect.setWidth(max(new_width, self.min_size))
            new_height = self.resize_start_rect.height() - delta.y()
            if new_height >= self.min_size: new_rect.setHeight(new_height); pos_delta.setY(delta.y()); adjust_pos = True
            else: new_rect.setHeight(self.min_size); pos_delta.setY(self.resize_start_rect.height() - self.min_size); adjust_pos = True
        elif self.resize_mode == self.RESIZE_BOTTOM_LEFT:
            new_width = self.resize_start_rect.width() - delta.x()
            if new_width >= self.min_size: new_rect.setWidth(new_width); pos_delta.setX(delta.x()); adjust_pos = True
            else: new_rect.setWidth(self.min_size); pos_delta.setX(self.resize_start_rect.width() - self.min_size); adjust_pos = True
            new_height = self.resize_start_rect.height() + delta.y()
            new_rect.setHeight(max(new_height, self.min_size))
        elif self.resize_mode == self.RESIZE_BOTTOM_RIGHT:
            new_width = self.resize_start_rect.width() + delta.x()
            new_height = self.resize_start_rect.height() + delta.y()
            new_rect.setWidth(max(new_width, self.min_size))
            new_rect.setHeight(max(new_height, self.min_size))

        self.prepareGeometryChange()
        self.rect = QtCore.QRectF(0, 0, new_rect.width(), new_rect.height())
        if adjust_pos:
            self.setPos(self.resize_start_item_pos + pos_delta)
        self.on_resize()

    def on_resize(self):
        pass

    def mouseReleaseEvent(self, event):
        self.resize_mode = self.RESIZE_NONE
        super().mouseReleaseEvent(event)


class ResizableLabelWidget(ResizableWidget):
    """可调整大小的标签组件"""

    def __init__(self, x, y, width, height, text="Label", color=QtCore.Qt.lightGray, editable=True): # 新增 editable
        # 将 editable 参数传递给父类构造函数
        super().__init__(x, y, width, height, color, editable=editable)

        self.label = QtWidgets.QLabel(text)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: black;
                font-size: 14px;
                padding: 5px;
            }
        """)
        self.proxy = QtWidgets.QGraphicsProxyWidget(self)
        self.proxy.setWidget(self.label)
        self._update_proxy_geometry()

    # ... (此类中的其他方法保持不变) ...
    def _update_proxy_geometry(self):
        """更新代理部件的几何形状"""
        margin = 5
        self.proxy.setGeometry(
            QtCore.QRectF(
                margin, margin,
                self.rect.width() - 2 * margin,
                self.rect.height() - 2 * margin
            )
        )

    def on_resize(self):
        """重写调整大小回调"""
        self._update_proxy_geometry()

    def set_text(self, text):
        self.label.setText(text)

    def set_font_size(self, size):
        font = self.label.font()
        font.setPointSize(size)
        self.label.setFont(font)

    def set_text_color(self, color):
        palette = self.label.palette()
        palette.setColor(QtGui.QPalette.WindowText, color)
        self.label.setPalette(palette)

    def set_text_alignment(self, alignment):
        self.label.setAlignment(alignment)

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        # 代理部件会自动绘制


stylesheet = """
    QGraphicsView {
        background: transparent; /* 背景透明 */
        border: none;           /* 移除边框 */
    }

    QScrollBar:vertical {
        border: none;            /* 移除滚动条边框 */
        background: transparent; /* 滚动条背景透明 */
        width: 1px;              /* 设置滚动条宽度为1像素，使其极细 */
        margin: 0px 0px 0px 0px; /* 移除所有外边距 */
    }

    QScrollBar::handle:vertical {
        background: transparent; /* 滑块（handle）背景透明 */
        min-height: 0px;         /* 由于滑块不可见且不可交互，最小高度可以为0 */
    }

    /* 完全隐藏上下箭头按钮 */
    QScrollBar::add-line:vertical, 
    QScrollBar::sub-line:vertical {
        border: none;
        background: none;
        height: 0px;
        min-height: 0px;
        max-height: 0px;
    }

    QScrollBar::up-arrow:vertical, 
    QScrollBar::down-arrow:vertical {
        background: none;
        border: none;
        height: 0px;
        width: 0px;
    }

    /* 确保滚动条轨道页面部分也透明 */
    QScrollBar::add-page:vertical, 
    QScrollBar::sub-page:vertical {
        background: transparent;
    }
"""


class ContentView(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self._items = []
        self.margin = 50
        self.min_width = 800
        self.min_height = 600
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag) # 用于选择
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))) # 透明背景
        self.setStyleSheet(stylesheet) # 应用样式表

        self.scene.changed.connect(self.on_scene_changed)
        self._expect_scroll_to_be_at_top_after_update = False

        # --- 新增编辑模式属性 ---
        self.edit_mode = True  # 默认为编辑模式

        # --- 新增拖拽调整大小相关属性 ---
        self.RESIZE_BORDER_WIDTH = 10  # 边缘检测宽度，与SuperSidebar保持一致
        
        # 启用鼠标跟踪以便检测鼠标移动和设置光标
        self.setMouseTracking(True)

        # --- 添加本地拖拽状态跟踪 ---
        self._is_forwarding_resize = False  # 跟踪是否正在转发拖拽事件
        
        # 强制光标控制
        self._force_cursor = None
        self._cursor_timer = QtCore.QTimer()
        self._cursor_timer.timeout.connect(self._enforce_cursor)
        self._cursor_timer.setSingleShot(False)
        self._cursor_timer.start(50)  # 每50ms检查一次光标

        self.update_scene_rect()

    def _is_in_parent_resize_area(self, pos):
        """检查鼠标位置是否在父窗口的调整大小区域内"""
        # 获取父窗口
        parent = self.parent()
        while parent and not hasattr(parent, 'is_edit_mode'):
            parent = parent.parent()
        
        if not parent or not hasattr(parent, 'is_edit_mode'):
            return False
            
        if not parent.is_edit_mode or not parent.is_pinned:
            return False
            
        # 将ContentView的坐标转换为SuperSidebar的坐标
        parent_pos = self.mapTo(parent, pos)
        
        # 检查是否在边缘区域，使用与SuperSidebar相同的逻辑
        if hasattr(parent, 'position'):
            # 调试信息
            print(f"DEBUG: Position={parent.position}, contentview_pos={pos}, parent_pos={parent_pos}, parent_width={parent.width()}")
            
            if parent.position == "right":
                # 右侧侧边栏，左边缘可调整 - 与SuperSidebar逻辑一致
                is_in_area = parent_pos.x() <= parent.RESIZE_BORDER_WIDTH
                print(f"DEBUG: Right sidebar - is_in_area={is_in_area}, threshold={parent.RESIZE_BORDER_WIDTH}")
                return is_in_area
            else:  # LEFT
                # 左侧侧边栏，右边缘可调整 - 与SuperSidebar逻辑一致
                threshold = parent.width() - parent.RESIZE_BORDER_WIDTH
                is_in_area = parent_pos.x() >= threshold
                print(f"DEBUG: Left sidebar - is_in_area={is_in_area}, threshold={threshold}")
                return is_in_area
        return False

    def _get_parent_sidebar(self):
        """获取父级SuperSidebar实例"""
        parent = self.parent()
        while parent and not hasattr(parent, 'is_edit_mode'):
            parent = parent.parent()
        return parent if parent and hasattr(parent, 'is_edit_mode') else None

    def mousePressEvent(self, event):
        """重写鼠标按下事件，处理边缘区域的拖拽"""
        if self._is_in_parent_resize_area(event.pos()):
            # 如果在父窗口的调整大小区域，将事件传递给父窗口
            parent = self._get_parent_sidebar()
            if parent:
                self._is_forwarding_resize = True  # 标记开始转发拖拽
                # 将ContentView的坐标转换为SuperSidebar的坐标
                # 需要递归向上转换到SuperSidebar
                parent_pos = self.mapTo(parent, event.pos())
                new_event = QtGui.QMouseEvent(
                    event.type(),
                    parent_pos,
                    event.globalPos(),
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                parent.mousePressEvent(new_event)
                return
        
        # 否则正常处理事件
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """重写鼠标移动事件，处理边缘区域的拖拽和光标设置"""
        # 如果正在转发拖拽，继续转发到父窗口
        if self._is_forwarding_resize:
            parent = self._get_parent_sidebar()
            if parent:
                # 将ContentView的坐标转换为SuperSidebar的坐标
                parent_pos = self.mapTo(parent, event.pos())
                new_event = QtGui.QMouseEvent(
                    event.type(),
                    parent_pos,
                    event.globalPos(),
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                parent.mouseMoveEvent(new_event)
                return
        
        # 检查是否在调整大小区域
        is_in_resize_area = self._is_in_parent_resize_area(event.pos())
        
        if is_in_resize_area:
            # 如果在父窗口的调整大小区域，强制设置调整大小光标
            print(f"DEBUG MouseMove: Force setting SizeHorCursor")
            self._force_cursor = QtCore.Qt.SizeHorCursor
            self.setCursor(QtCore.Qt.SizeHorCursor)
            # 也在viewport上设置光标
            self.viewport().setCursor(QtCore.Qt.SizeHorCursor)
            print(f"DEBUG: Set SizeHorCursor on both view and viewport")
            # 不调用父类方法，避免光标被覆盖
        else:
            # 不在调整大小区域，停止强制光标并调用父类方法
            self._force_cursor = None
            # 重置view和viewport的光标
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.viewport().setCursor(QtCore.Qt.ArrowCursor)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """重写鼠标释放事件，处理边缘区域的拖拽"""
        # 如果正在转发拖拽，先转发事件，然后重置状态
        if self._is_forwarding_resize:
            parent = self._get_parent_sidebar()
            if parent:
                # 将ContentView的坐标转换为SuperSidebar的坐标
                parent_pos = self.mapTo(parent, event.pos())
                new_event = QtGui.QMouseEvent(
                    event.type(),
                    parent_pos,
                    event.globalPos(),
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
                parent.mouseReleaseEvent(new_event)
            
            # 重置转发状态并恢复光标
            self._is_forwarding_resize = False
            self.setCursor(QtCore.Qt.ArrowCursor)
            return
        
        # 否则正常处理事件
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件，确保重置状态"""
        if self._is_forwarding_resize:
            # 如果鼠标离开时还在拖拽状态，强制重置
            self._is_forwarding_resize = False
        
        # 停止强制光标，重置view和viewport的光标
        self._force_cursor = None
        self.setCursor(QtCore.Qt.ArrowCursor)
        self.viewport().setCursor(QtCore.Qt.ArrowCursor)
        super().leaveEvent(event)

    def on_scene_changed(self):
        self.update_scene_rect()

    def update_scene_rect(self):
        v_bar = self.verticalScrollBar()
        is_at_top_before_update = not v_bar.isVisible() or (v_bar.value() == v_bar.minimum())

        if not self._items:
            target_rect = QtCore.QRectF(0, 0, self.min_width, self.min_height)
        else:
            items_rect = QtCore.QRectF()
            for item in self._items:
                if item and item.scene(): # 确保 item 仍然在场景中
                    item_scene_rect = item.sceneBoundingRect()
                    if items_rect.isNull():
                        items_rect = item_scene_rect
                    else:
                        items_rect = items_rect.united(item_scene_rect)
            if items_rect.isNull():
                target_rect = QtCore.QRectF(0, 0, self.min_width, self.min_height)
            else:
                scene_x = 0.0
                scene_y = 0.0
                scene_width = self.min_width
                content_bottom_y = items_rect.bottom()
                scene_height = max(self.min_height, content_bottom_y)
                target_rect = QtCore.QRectF(scene_x, scene_y, scene_width, scene_height)

        if self.scene.sceneRect() != target_rect:
            self.scene.setSceneRect(target_rect)
            if is_at_top_before_update and self.verticalScrollBar().isVisible():
                self._expect_scroll_to_be_at_top_after_update = True
                QtCore.QTimer.singleShot(0, self._delayed_scroll_check)
            else:
                self._expect_scroll_to_be_at_top_after_update = False

    def _delayed_scroll_check(self):
        if self._expect_scroll_to_be_at_top_after_update:
            v_bar = self.verticalScrollBar()
            if v_bar.isVisible() and v_bar.value() != v_bar.minimum():
                v_bar.setValue(v_bar.minimum())
        self._expect_scroll_to_be_at_top_after_update = False

    def add_label_widget(self, x=None, y=None, width=200, height=100, text="Label",
                         color=QtCore.Qt.lightGray):
        if x is None or y is None:
            x = 50
            y_offset = 0 # 基础y偏移
            if self._items:
                # 确保只考虑仍在场景中的最后一个item
                valid_items = [item for item in self._items if item.scene()]
                if valid_items:
                    last_item = valid_items[-1]
                    last_rect = last_item.sceneBoundingRect()
                    y_offset = last_rect.bottom() + 20
                else: # 如果_items不为空，但没有有效item（例如都被移除了）
                    y_offset = 0
            else:
                y_offset = 0
            y = y_offset

        # --- 在创建组件时传递当前的编辑模式 ---
        widget = ResizableLabelWidget(x, y, width, height, text, color, editable=self.edit_mode)

        self.scene.addItem(widget)
        self._items.append(widget)
        self.update_scene_rect()
        return widget

    # --- 新增设置编辑模式的方法 ---
    def set_edit_mode(self, editable: bool):
        """设置视图的编辑模式"""
        if self.edit_mode == editable:
            return
        self.edit_mode = editable
        for item in self._items:
            if isinstance(item, ResizableWidget): # 确保是可编辑的组件类型
                item.set_editable(editable)

        if not editable:
            # 退出编辑模式时，清空场景中的选择
            self.scene.clearSelection()
            # 可选：如果希望在非编辑模式下禁用橡皮筋选择
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        else:
            # 进入编辑模式时，恢复橡皮筋选择（如果之前禁用了）
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)

        # 打印当前模式以供调试
        print(f"Edit mode set to: {self.edit_mode}")

    def _enforce_cursor(self):
        """强制执行光标设置"""
        if self._force_cursor is not None:
            current_cursor = self.cursor().shape()
            viewport_cursor = self.viewport().cursor().shape()
            if current_cursor != self._force_cursor or viewport_cursor != self._force_cursor:
                print(f"DEBUG: Enforcing cursor change - view: {current_cursor} -> {self._force_cursor}, viewport: {viewport_cursor} -> {self._force_cursor}")
                self.setCursor(self._force_cursor)
                self.viewport().setCursor(self._force_cursor)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    main_window = QtWidgets.QMainWindow() # 或者任何你的主窗口容器
    content_view = ContentView()

    # 添加一些组件
    label1 = content_view.add_label_widget(x=50, y=50, text="组件1")
    label2 = content_view.add_label_widget(x=50, y=180, text="组件2")

    # 创建一个按钮来切换编辑模式 (示例)
    edit_mode_button = QtWidgets.QPushButton("切换编辑模式")
    def toggle_edit_mode():
        content_view.set_edit_mode(not content_view.edit_mode)
        # 更新按钮文本以反映当前状态 (可选)
        current_mode_text = "编辑模式" if content_view.edit_mode else "预览模式"
        edit_mode_button.setText(f"切换到{('预览' if content_view.edit_mode else '编辑')}模式 (当前: {current_mode_text})")


    edit_mode_button.clicked.connect(toggle_edit_mode)
    toggle_edit_mode() # 调用一次以设置初始按钮文本

    # 布局示例
    central_widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(central_widget)
    layout.addWidget(edit_mode_button)
    layout.addWidget(content_view)
    main_window.setCentralWidget(central_widget)

    main_window.setGeometry(100, 100, 900, 700)
    main_window.show()

    sys.exit(app.exec_())
