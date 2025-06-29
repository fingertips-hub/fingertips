import uuid

import qfluentwidgets
from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

from fingertips.widget_utils import signal_bus
from fingertips.settings.config_model import config_model


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

    def __init__(self, x, y, width, height, editable=True):
        super().__init__()
        self.rect = QtCore.QRectF(0, 0, width, height)
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

        old_editable = self.editable
        self.editable = editable
        
        # 对于ResizableWidgetBase，需要特殊处理头部区域
        if isinstance(self, ResizableWidgetBase):
            # 调整组件总高度以适应头部区域的添加/移除
            if editable and not old_editable:
                # 进入编辑模式：添加头部区域
                self.prepareGeometryChange()
                self.rect = QtCore.QRectF(0, 0, self.rect.width(), self.rect.height() + self.header_height)
                self._update_proxy_geometry()
            elif not editable and old_editable:
                # 退出编辑模式：移除头部区域
                self.prepareGeometryChange()
                self.rect = QtCore.QRectF(0, 0, self.rect.width(), self.rect.height() - self.header_height)
                self._update_proxy_geometry()
                # 重置头部拖拽状态
                self.header_dragging = False
                # 重置关闭按钮悬停状态
                if hasattr(self, 'close_button_hovered'):
                    self.close_button_hovered = False
        
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)  # 禁用默认拖拽，使用自定义头部拖拽
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, editable)

        if not editable:
            # 如果变为不可编辑，则取消选择并重置状态
            if self.isSelected():
                self.setSelected(False)
            self.resize_mode = self.RESIZE_NONE
            self.setCursor(QtCore.Qt.ArrowCursor) # 重置光标

        self.update() # 请求重绘

    def boundingRect(self):
        return self.rect.adjusted(-self.handle_size, -self.handle_size,
                                  self.handle_size, self.handle_size)

    def paint(self, painter, option, widget):
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
        
        # 对于有头部区域的组件，所有手柄仍然按照完整rect绘制
        # 这样用户可以通过拖拽手柄来调整整个组件（包括头部）的大小
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
        # 只有选中的组件才能调整大小，但要允许未选中的组件拖拽移动
        if not self.isSelected():
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

    def _handle_selection(self, modifiers=QtCore.Qt.NoModifier):
        """处理选择逻辑，支持单选和多选"""
        if self.scene():
            # 如果按住Ctrl键，则为多选模式
            if modifiers & QtCore.Qt.ControlModifier:
                # 多选模式：切换当前组件的选择状态
                self.setSelected(not self.isSelected())
            else:
                # 单选模式：清除其他选择，选中自己
                if not self.isSelected():
                    self.scene().clearSelection()
                    self.setSelected(True)

    def _clear_other_selections_and_select_self(self):
        """清除场景中其他组件的选择状态，然后选中自己"""
        if self.scene():
            # 清除场景中所有选择
            self.scene().clearSelection()
            # 选中自己
            self.setSelected(True)

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
        if not self.editable:
            super().mouseMoveEvent(event) # 允许焦点等非编辑交互
            return

        # 可编辑时的逻辑
        if self.resize_mode != self.RESIZE_NONE:
            self._perform_resize(event.scenePos())
            event.accept()
        else:
            # 如果不是调整大小，则交给基类处理（例如移动）
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


class Context:
    def dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


class ResizableWidgetBase(ResizableWidget):
    """可调整大小的按钮组件"""
    def __init__(self, x, y, widget, widget_class=None, editable=True, wid=None, custom_width=None, custom_height=None):
        # 计算包含头部区域的总高度
        self.header_height = 22  # 头部区域高度
        
        # 使用自定义尺寸或者widget的默认尺寸
        if custom_width is not None and custom_height is not None:
            # 使用自定义尺寸（通常在加载配置时使用）
            width = custom_width
            height = custom_height
        else:
            # 使用widget的默认尺寸（通常在创建新组件时使用）
            width = widget.width()
            height = widget.height() + (self.header_height if editable else 0)
        
        # 将 editable 参数传递给父类构造函数
        super().__init__(x, y, width, height, editable=editable)
        self.wid = wid or str(uuid.uuid4())
        widget.context = Context()
        widget.context.wid = self.wid

        self.proxy = QtWidgets.QGraphicsProxyWidget(self)
        self.proxy.setWidget(widget)
        
        # 保存原始widget的引用，用于调整大小
        self.widget = widget
        
        # 头部相关属性
        self.header_dragging = False
        self.header_drag_start_pos = QtCore.QPointF()
        self.header_drag_start_item_pos = QtCore.QPointF()
        self.close_button_hovered = False  # 跟踪关闭按钮悬停状态
        
        self._update_proxy_geometry()
        
        # 保存widget类信息，用于序列化
        self.widget_class = widget_class

    def _update_proxy_geometry(self):
        """更新代理部件的几何形状"""
        margin = 0
        
        # 计算组件内容区域的位置和大小（考虑头部区域）
        header_offset = self.header_height if self.editable else 0
        content_y = margin + header_offset
        content_height = self.rect.height() - 2 * margin - header_offset
        
        # 设置代理组件的几何形状
        self.proxy.setGeometry(
            QtCore.QRectF(
                margin, content_y,
                self.rect.width() - 2 * margin,
                content_height
            )
        )
        
        # 确保内部widget也调整到正确的大小
        if self.widget and hasattr(self.widget, 'resize'):
            new_width = int(self.rect.width() - 2 * margin)
            new_height = int(content_height)
            
            # 更新widget的大小
            self.widget.resize(new_width, new_height)
            
            # 如果widget有setFixedSize方法，也更新它
            if hasattr(self.widget, 'setFixedSize'):
                self.widget.setFixedSize(new_width, new_height)
            
            # 如果widget有setMinimumSize和setMaximumSize方法，也更新它们
            if hasattr(self.widget, 'setMinimumSize'):
                self.widget.setMinimumSize(new_width, new_height)
            if hasattr(self.widget, 'setMaximumSize'):
                self.widget.setMaximumSize(new_width, new_height)

    def on_resize(self):
        """重写调整大小回调"""
        self._update_proxy_geometry()

    def paint(self, painter, option, widget):
        # 在编辑模式下绘制头部区域
        if self.editable:
            self._draw_header(painter)
        
        # 绘制选中状态的边框和手柄（确保在头部区域之后绘制，这样会覆盖在头部上方）
        if self.isSelected():
            pen = QtGui.QPen(QtCore.Qt.black, 2)
            painter.setPen(pen)
            painter.drawRect(self.rect)
            self._draw_resize_handles(painter)

    def _draw_header(self, painter):
        """绘制头部区域"""
        header_rect = QtCore.QRectF(0, 0, self.rect.width(), self.header_height)
        
        # 绘制头部背景 - 更透明
        painter.setPen(QtGui.QPen(QtGui.QColor(120, 20, 20, 80), 1))  # 更透明的边框
        painter.setBrush(QtGui.QBrush(QtGui.QColor(240, 240, 240, 60)))  # 更透明的背景（从200降到60）
        painter.drawRect(header_rect)
        
        # 绘制头部文本
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.setFont(QtGui.QFont("Arial", 9))
        text_rect = header_rect.adjusted(5, 0, -30, 0)  # 留出关闭按钮的空间
        widget_name = self.widget.name if self.widget_class else "Widget"
        painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, widget_name)
        
        # 绘制关闭按钮
        self._draw_close_button(painter)

    def _draw_close_button(self, painter):
        """绘制关闭按钮"""
        button_size = 16
        button_margin = 4
        button_rect = QtCore.QRectF(
            self.rect.width() - button_size - button_margin,
            button_margin,
            button_size,
            button_size
        )
        
        # 绘制 X 符号 - 根据悬停状态使用不同颜色
        if self.close_button_hovered:
            painter.setPen(QtGui.QPen(QtGui.QColor(200, 0, 0, 220), 2))  # 悬停时使用红色
        else:
            painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80, 180), 2))  # 默认深灰色
        
        margin = 4
        painter.drawLine(
            button_rect.left() + margin, button_rect.top() + margin,
            button_rect.right() - margin, button_rect.bottom() - margin
        )
        painter.drawLine(
            button_rect.right() - margin, button_rect.top() + margin,
            button_rect.left() + margin, button_rect.bottom() - margin
        )

    def _get_header_rect(self):
        """获取头部区域矩形"""
        if not self.editable:
            return QtCore.QRectF()
        return QtCore.QRectF(0, 0, self.rect.width(), self.header_height)

    def _get_close_button_rect(self):
        """获取关闭按钮矩形"""
        if not self.editable:
            return QtCore.QRectF()
        
        button_size = 16
        button_margin = 4
        return QtCore.QRectF(
            self.rect.width() - button_size - button_margin,
            button_margin,
            button_size,
            button_size
        )

    def _is_in_header(self, pos):
        """检查位置是否在头部区域"""
        return self._get_header_rect().contains(pos)

    def _is_in_close_button(self, pos):
        """检查位置是否在关闭按钮"""
        return self._get_close_button_rect().contains(pos)

    def _clear_other_selections_and_select_self(self):
        """清除场景中其他组件的选择状态，然后选中自己"""
        if self.scene():
            # 清除场景中所有选择
            self.scene().clearSelection()
            # 选中自己
            self.setSelected(True)

    def mousePressEvent(self, event):
        """重写鼠标按下事件，处理头部拖拽和关闭按钮"""
        if not self.editable:
            super().mousePressEvent(event)
            return

        # 首先判断是否点击在代理组件（子组件内容）区域内
        if self.proxy and self.proxy.contains(self.proxy.mapFromParent(event.pos())):
            # 点击在子组件内容区域，让子组件自己处理事件
            super().mousePressEvent(event)
            return

        # 检查是否点击关闭按钮
        if self._is_in_close_button(event.pos()):
            # 确保组件被选中（关闭按钮不支持多选逻辑）
            if not self.isSelected():
                self.scene().clearSelection()
                self.setSelected(True)
            self._handle_close_button_click()
            event.accept()
            return

        # 检查是否在头部区域
        if self._is_in_header(event.pos()):
            # 处理选择逻辑，支持多选
            self._handle_selection(event.modifiers())
            
            # 然后准备拖拽
            self.header_dragging = True
            self.header_drag_start_pos = event.scenePos()
            self.header_drag_start_item_pos = self.pos()
            # 记录所有选中组件的初始位置（用于群组移动）
            self._group_drag_start_positions = {}
            if self.scene():
                for item in self.scene().selectedItems():
                    if isinstance(item, ResizableWidgetBase):
                        self._group_drag_start_positions[item] = item.pos()
            event.accept()
            return

        # 其他情况交给父类处理（包括调整大小）
        # 但确保在点击组件内容区域时也有正确的选择行为
        self._handle_selection(event.modifiers())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """重写鼠标移动事件，处理头部拖拽"""
        if not self.editable:
            super().mouseMoveEvent(event)
            return

        # 如果正在进行头部拖拽，继续处理拖拽
        if self.header_dragging:
            delta = event.scenePos() - self.header_drag_start_pos
            
            # 如果有多个选中的组件，则进行群组移动
            if hasattr(self, '_group_drag_start_positions') and len(self._group_drag_start_positions) > 1:
                # 群组移动：移动所有选中的组件
                for item, start_pos in self._group_drag_start_positions.items():
                    if item.scene():  # 确保组件仍在场景中
                        new_pos = start_pos + delta
                        item.setPos(new_pos)
            else:
                # 单个组件移动
                new_pos = self.header_drag_start_item_pos + delta
                self.setPos(new_pos)
            
            event.accept()
            return

        # 检查是否在子组件内容区域
        if self.proxy and self.proxy.contains(self.proxy.mapFromParent(event.pos())):
            # 在子组件内容区域，让子组件自己处理事件
            super().mouseMoveEvent(event)
            return

        # 其他情况交给父类处理
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """重写鼠标释放事件"""
        if self.header_dragging:
            self.header_dragging = False
            # 清理群组拖拽状态
            if hasattr(self, '_group_drag_start_positions'):
                delattr(self, '_group_drag_start_positions')
            event.accept()
            return

        # 检查是否在子组件内容区域
        if self.proxy and self.proxy.contains(self.proxy.mapFromParent(event.pos())):
            # 在子组件内容区域，让子组件自己处理事件
            super().mouseReleaseEvent(event)
            return

        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        """处理鼠标悬停，设置合适的光标"""
        if self.editable:
            if self._is_in_close_button(event.pos()):
                if not self.close_button_hovered:
                    self.close_button_hovered = True
                    self.update()  # 触发重绘以显示悬停效果
                self.setCursor(QtCore.Qt.PointingHandCursor)
            elif self._is_in_header(event.pos()):
                if self.close_button_hovered:
                    self.close_button_hovered = False
                    self.update()  # 触发重绘以移除悬停效果
                self.setCursor(QtCore.Qt.SizeAllCursor)  # 显示移动光标
            else:
                if self.close_button_hovered:
                    self.close_button_hovered = False
                    self.update()  # 触发重绘以移除悬停效果
                # 调用父类方法处理调整大小的悬停
                super().hoverMoveEvent(event)
        else:
            super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        """鼠标离开事件，重置悬停状态"""
        if hasattr(self, 'close_button_hovered') and self.close_button_hovered:
            self.close_button_hovered = False
            self.update()  # 触发重绘以移除悬停效果
        super().hoverLeaveEvent(event)

    def _handle_close_button_click(self):
        """处理关闭按钮点击"""
        # 通知ContentView删除这个组件
        scene = self.scene()
        if scene and hasattr(scene, 'views') and scene.views():
            view = scene.views()[0]  # 获取第一个视图
            if hasattr(view, '_items') and self in view._items:
                # 显示确认对话框
                from PySide2.QtWidgets import QMessageBox
                widget_name = self.widget_class.__name__ if self.widget_class else "组件"
                reply = QMessageBox.question(
                    None,
                    '确认删除',
                    f'确定要删除 {widget_name} 吗？\n\n此操作无法撤销。',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 从场景和列表中移除
                    if self.scene():
                        self.scene().removeItem(self)
                    if self in view._items:
                        view._items.remove(self)
                    view.update_scene_rect()
        
    def serialize(self):
        """序列化widget信息"""
        # 计算实际内容高度：只有在编辑模式下才需要减去头部高度
        content_height = self.rect.height()
        if self.editable:
            content_height -= self.header_height
        
        return {
            'wid': self.wid,
            'widget_class': self.widget_class.__name__ if self.widget_class else None,
            'widget_module': self.widget_class.__module__ if self.widget_class else None,
            'x': self.pos().x(),
            'y': self.pos().y(),
            'width': self.rect.width(),
            'height': content_height,  # 实际内容高度
            'config': self.widget.get_config(),
        }


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
        # 启用场景的选择区域
        self.setRubberBandSelectionMode(QtCore.Qt.IntersectsItemShape)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))) # 透明背景
        self.setStyleSheet(stylesheet) # 应用样式表

        self.scene.changed.connect(self.on_scene_changed)
        self._expect_scroll_to_be_at_top_after_update = False

        # --- 新增编辑模式属性 ---
        self.edit_mode = False  # 默认为编辑模式

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
        
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

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
        
        # 首先检查鼠标是否在某个组件上，如果是则不应该触发父窗口的调整大小
        item_at_pos = self.itemAt(pos)
        if item_at_pos:
            # 检查是否是代理组件或其子组件
            if isinstance(item_at_pos, QtWidgets.QGraphicsProxyWidget):
                # 鼠标在代理组件（即子组件内部），不触发父窗口调整大小
                return False
            elif isinstance(item_at_pos, (ResizableWidget, ResizableWidgetBase)):
                # 检查是否点击在组件的头部区域（仅编辑模式下存在）
                if isinstance(item_at_pos, ResizableWidgetBase) and item_at_pos.editable:
                    # 将鼠标位置转换为组件本地坐标
                    local_pos = item_at_pos.mapFromScene(self.mapToScene(pos))
                    # 如果不在头部区域且不在调整大小区域，说明在组件内容区域
                    if not item_at_pos._is_in_header(local_pos) and item_at_pos._get_resize_mode(local_pos) == item_at_pos.RESIZE_NONE:
                        # 在组件内容区域，不触发父窗口调整大小
                        return False
                # 其他情况（头部、调整大小手柄等）可以继续检查边缘拖拽
            
        # 将ContentView的坐标转换为SuperSidebar的坐标
        parent_pos = self.mapTo(parent, pos)
        
        # 检查是否在边缘区域，使用与SuperSidebar相同的逻辑
        if hasattr(parent, 'position'):
            if parent.position == "right":
                # 右侧侧边栏，左边缘可调整 - 与SuperSidebar逻辑一致
                is_in_area = parent_pos.x() <= parent.RESIZE_BORDER_WIDTH
                return is_in_area
            else:  # LEFT
                # 左侧侧边栏，右边缘可调整 - 与SuperSidebar逻辑一致
                threshold = parent.width() - parent.RESIZE_BORDER_WIDTH
                is_in_area = parent_pos.x() >= threshold
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
        # 首先检查鼠标位置下是否有子组件
        item_at_pos = self.itemAt(event.pos())
        
        # 如果鼠标在子组件内部，让子组件处理事件，不进行穿透
        if item_at_pos and isinstance(item_at_pos, QtWidgets.QGraphicsProxyWidget):
            # 调用父类方法，让子组件正常处理事件
            super().mousePressEvent(event)
            # 确保获得焦点以接收键盘事件
            if not self.hasFocus():
                self.setFocus()
            return
        
        # 检查是否在父窗口的调整大小区域
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
        
        # 如果点击在空白区域（没有组件），根据修饰键决定是否清除选择
        if not item_at_pos and self.edit_mode:
            # 只有在没有按Ctrl键时才清除选择，这样支持框选多选
            if not (event.modifiers() & QtCore.Qt.ControlModifier):
                self.scene.clearSelection()
        
        # 确保获得焦点以接收键盘事件
        if not self.hasFocus():
            self.setFocus()

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
        
        # 首先检查鼠标位置下是否有子组件
        item_at_pos = self.itemAt(event.pos())
        
        # 如果鼠标在子组件内部，让子组件处理事件，不进行穿透
        if item_at_pos and isinstance(item_at_pos, QtWidgets.QGraphicsProxyWidget):
            # 停止强制光标，让子组件自己处理光标
            self._force_cursor = None
            super().mouseMoveEvent(event)
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
        
        # 检查鼠标位置下是否有子组件
        item_at_pos = self.itemAt(event.pos())
        
        # 如果鼠标在子组件内部，让子组件处理事件，不进行穿透
        if item_at_pos and isinstance(item_at_pos, QtWidgets.QGraphicsProxyWidget):
            super().mouseReleaseEvent(event)
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

    def add_widget(self, x=None, y=None, widget=None, wid=None, skip_collision_check=False):
        # --- 在创建组件时传递当前的编辑模式和widget类 ---
        widget_instance = widget() if callable(widget) else widget
        widget_instance.edit_mode_changed(self.edit_mode)

        widget_class = widget if callable(widget) else widget.__class__
        
        # 如果没有指定位置，将组件放置在视图中心
        if x is None or y is None:
            # 获取当前视图的可见区域
            visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
            
            # 计算组件大小（包括头部区域）
            widget_width = widget_instance.width()
            widget_height = widget_instance.height()
            if self.edit_mode:
                widget_height += 22  # 添加头部区域高度
            
            # 计算中心位置（组件左上角坐标）
            x = visible_rect.center().x() - widget_width / 2
            y = visible_rect.center().y() - widget_height / 2
            
            # 确保组件不会超出场景边界
            x = max(0, x)
            y = max(0, y)
            
            # 只有在没有跳过碰撞检查时才进行防重叠逻辑
            if not skip_collision_check:
                # 如果位置与现有组件重叠，循环偏移直到找到空位
                offset = 0
                max_attempts = 10  # 最多尝试10次偏移
                attempt = 0
                
                while attempt < max_attempts:
                    new_rect = QtCore.QRectF(x + offset, y + offset, widget_width, widget_height)
                    has_collision = False
                    
                    for existing_item in self._items:
                        if existing_item and existing_item.scene():
                            existing_rect = existing_item.sceneBoundingRect()
                            if existing_rect.intersects(new_rect):
                                has_collision = True
                                break
                    
                    if not has_collision:
                        # 找到无碰撞的位置
                        x += offset
                        y += offset
                        break
                    
                    # 有碰撞，增加偏移量继续尝试
                    offset += 30
                    attempt += 1

        resizable_widget = ResizableWidgetBase(
            x, y, widget_instance, widget_class=widget_class, editable=self.edit_mode, wid=wid)

        self.scene.addItem(resizable_widget)
        self._items.append(resizable_widget)
        self.update_scene_rect()
        return resizable_widget

    # --- 新增设置编辑模式的方法 ---
    def set_edit_mode(self, editable: bool):
        """设置视图的编辑模式"""
        if self.edit_mode == editable:
            return
        
        # 如果从编辑模式切换到非编辑模式，保存节点信息
        if self.edit_mode and not editable:
            self.save_nodes_to_config()

        self.edit_mode = editable
        for item in self._items:
            if isinstance(item, ResizableWidget):
                item.set_editable(editable)

        if not editable:
            # 退出编辑模式时，清空场景中的选择
            self.scene.clearSelection()
            # 禁用选择
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        else:
            # 进入编辑模式时，启用框选模式以支持多选
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
            # 确保在编辑模式下能接收键盘事件
            self.setFocus()

        signal_bus.super_sidebar_edit_mode_changed.emit(self.edit_mode)
        
    def save_nodes_to_config(self):
        """将节点信息保存到配置文件"""
        nodes_data = []
        for i, item in enumerate(self._items):
            if isinstance(item, ResizableWidgetBase) and item.scene():
                try:
                    node_data = item.serialize()
                    if node_data['widget_class']:  # 只保存有效的widget类
                        print(f"Saving {node_data['widget_class']} at ({node_data['x']}, {node_data['y']}) with size ({node_data['width']}, {node_data['height']}) editable={item.editable}")
                        nodes_data.append(node_data)
                    else:
                        print(f"Skipping item {i}: no widget class")
                except Exception as e:
                    print(f"Error serializing item {i}: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"Saving {len(nodes_data)} nodes to config")
        
        # 保存到配置
        config_data = {'nodes': nodes_data}
        qfluentwidgets.qconfig.set(config_model.super_sidebar_node, config_data)

    def load_nodes_from_config(self):
        """从配置文件加载节点信息"""
        import importlib
        
        config_data = config_model.super_sidebar_node.value
        if not config_data or 'nodes' not in config_data:
            print("No config data found or no nodes in config")
            return
            
        print(f"Loading {len(config_data['nodes'])} nodes from config")
        
        # 清空现有节点
        for item in self._items[:]:
            if item.scene():
                self.scene.removeItem(item)
        self._items.clear()
        
        # 加载节点
        for i, node_data in enumerate(config_data['nodes']):
            try:
                # 动态导入widget类
                module_name = node_data.get('widget_module')
                class_name = node_data.get('widget_class')
                
                if not module_name or not class_name:
                    print(f"Skipping node {i}: missing module or class name")
                    continue
                    
                module = importlib.import_module(module_name)
                widget_class = getattr(module, class_name)
                
                # 获取保存的精确位置和尺寸
                saved_x = node_data.get('x', 0)
                saved_y = node_data.get('y', 0)
                saved_width = node_data.get('width', 300)
                saved_height = node_data.get('height', 200)
                
                print(f"Loading {class_name} at position ({saved_x}, {saved_y}) with size ({saved_width}, {saved_height})")
                
                # 创建widget实例
                widget_instance = widget_class()
                widget_instance.set_config(node_data.get('config', {}))
                widget_instance.save_config_signal.connect(self.save_nodes_to_config)

                # 计算正确的总高度
                if self.edit_mode:
                    # 在编辑模式下，需要为内容高度加上头部高度
                    total_height = saved_height + 22  # header_height
                else:
                    # 非编辑模式下，直接使用保存的高度
                    total_height = saved_height
                
                # 创建可调整大小的wrapper，直接使用保存的精确位置和尺寸
                resizable_widget = ResizableWidgetBase(
                    saved_x,
                    saved_y,
                    widget_instance,
                    widget_class=widget_class,
                    editable=self.edit_mode,
                    wid=node_data.get('wid'),
                    custom_width=saved_width,
                    custom_height=total_height
                )
                
                print(f"Set {class_name} to position ({resizable_widget.pos().x()}, {resizable_widget.pos().y()}) with rect size ({resizable_widget.rect.width()}, {resizable_widget.rect.height()})")
                
                # 添加到场景
                self.scene.addItem(resizable_widget)
                self._items.append(resizable_widget)
                
            except Exception as e:
                print(f"Failed to load widget {class_name}: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"Successfully loaded {len(self._items)} widgets")
        self.update_scene_rect()

    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
            if self.edit_mode:
                self.delete_selected_items()
                event.accept()
                return
        
        # 调用父类方法处理其他键盘事件
        super().keyPressEvent(event)
    
    def delete_selected_items(self):
        """删除选中的组件"""
        # 获取所有选中的项目
        selected_items = self.scene.selectedItems()
        
        if not selected_items:
            return
            
        # 过滤出ResizableWidgetBase类型的项目
        items_to_delete = [item for item in selected_items if isinstance(item, ResizableWidgetBase)]
        
        if not items_to_delete:
            return
        
        # 显示确认对话框（可选）
        # 如果您不想要确认对话框，可以注释掉以下几行
        from PySide2.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            None, 
            '确认删除', 
            f'确定要删除选中的 {len(items_to_delete)} 个组件吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # 从场景和列表中删除项目
        for item in items_to_delete:
            # 从场景中移除
            if item.scene():
                self.scene.removeItem(item)
            
            # 从内部列表中移除
            if item in self._items:
                self._items.remove(item)
                
            # 清理引用
            if hasattr(item, 'proxy'):
                item.proxy = None
            if hasattr(item, 'widget'):
                item.widget = None

        # 更新场景矩形
        self.update_scene_rect()

    def _enforce_cursor(self):
        """强制执行光标设置"""
        if self._force_cursor is not None:
            current_cursor = self.cursor().shape()
            viewport_cursor = self.viewport().cursor().shape()
            if current_cursor != self._force_cursor or viewport_cursor != self._force_cursor:
                self.setCursor(self._force_cursor)
                self.viewport().setCursor(self._force_cursor)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    main_window = QtWidgets.QMainWindow() # 或者任何你的主窗口容器
    content_view = ContentView()

    # 添加一些组件
    label1 = content_view.add_widget(x=50, y=50, text="组件1")
    label2 = content_view.add_widget(x=50, y=180, text="组件2")

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
