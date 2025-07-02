import uuid
from datetime import datetime
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt, QTimer
import qtawesome
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget


class ClipboardItemWidget(QtWidgets.QWidget):
    """单个剪切板项目组件"""
    
    # 信号定义
    item_clicked = QtCore.Signal(str)  # 点击信号，传递内容
    item_deleted = QtCore.Signal(str)  # 删除信号，传递ID
    
    def __init__(self, item_id, content, timestamp, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.content = content
        self.timestamp = timestamp
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        self.setFixedHeight(50)
        # 设置鼠标指针为手形，表示可点击
        self.setCursor(Qt.PointingHandCursor)
        
        # 设置默认样式
        self.normal_style = """
            QWidget {
                background-color: white;
                border: 2px solid #333333;
                border-radius: 8px;
                margin: 2px;
            }
            QLabel#contentLabel {
                color: #333;
                background: transparent;
                border: none;
            }
            QLabel#timeLabel {
                color: #888;
                background: transparent;
                border: none;
            }
        """
        
        self.hover_style = """
            QWidget {
            }
            QLabel#contentLabel {
                color: #1976d2;
                background: transparent;
                border: none;
                font-weight: 600;
            }
            QLabel#timeLabel {
                color: #4CAF50;
                background: transparent;
                border: none;
                font-weight: 500;
            }
        """
        
        self.setStyleSheet(self.normal_style)
        
        # 主布局
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(8)
        
        # 内容显示区域
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.setSpacing(2)
        
        # 截取内容用于显示（一行）
        display_content = self.content.replace('\n', ' ').replace('\r', ' ').strip()
        if len(display_content) > 60:
            display_content = display_content[:60] + "..."
        
        # 内容标签
        self.content_label = QtWidgets.QLabel(display_content)
        self.content_label.setObjectName("contentLabel")
        self.content_label.setStyleSheet("""
            font-size: 13px;
            font-weight: normal;
        """)
        self.content_label.setWordWrap(False)
        # 设置完整内容为工具提示，并添加双击提示
        self.content_label.setToolTip(self.content)
        content_layout.addWidget(self.content_label)
        
        # 时间标签
        time_str = self.format_timestamp(self.timestamp)
        self.time_label = QtWidgets.QLabel(time_str)
        self.time_label.setObjectName("timeLabel")
        self.time_label.setStyleSheet("""
            font-size: 11px;
        """)
        content_layout.addWidget(self.time_label)
        
        main_layout.addLayout(content_layout, 1)
        
        # 删除按钮
        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setIcon(qtawesome.icon('fa.trash', color='#ff5722'))
        self.delete_button.setFixedSize(24, 24)
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setStyleSheet("""
            QPushButton#deleteButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                padding: 4px;
            }
            QPushButton#deleteButton:hover {
                background-color: #ffcdd2;
            }
            QPushButton#deleteButton:pressed {
                background-color: #ffb3ba;
            }
        """)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        main_layout.addWidget(self.delete_button)
        
    def format_timestamp(self, timestamp):
        """格式化时间戳显示"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp)
            else:
                dt = timestamp
                
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days}天前"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}小时前"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}分钟前"
            else:
                return "刚刚"
        except:
            return "未知时间"
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.setStyleSheet(self.normal_style)
        super().leaveEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """处理鼠标双击事件"""
        if event.button() == Qt.LeftButton:
            # 双击时复制内容到剪切板
            self.item_clicked.emit(self.content)
        super().mouseDoubleClickEvent(event)
        
    def on_delete_clicked(self):
        """处理删除按钮点击"""
        self.item_deleted.emit(self.item_id)


class HistoricalCuttingBoardCard(SidebarWidget):
    """历史剪切板组件"""
    
    name = '历史剪切板'
    category = '生活'
    icon = 'fa.clipboard'
    description = '记录和管理剪切板历史，支持一键复制和删除'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print("🔧 初始化历史剪切板组件...")
        self.clipboard_items = []  # 存储剪切板历史数据
        self.current_page = 0  # 当前页面
        self.page_size = 20  # 每页显示数量
        self.last_clipboard_content = ""  # 上次剪切板内容，用于去重
        self.db_error_count = 0  # 数据库错误计数
        self.db_disabled = False  # 数据库功能禁用标志
        
        print("⚙️ 设置用户界面...")
        self.setup_ui()
        
        print("📋 设置剪切板监听...")
        self.setup_clipboard_listener()

    def on_loaded(self):
        print("🔄 ON_LOADED 被调用 - 开始加载历史记录...")
        self.load_history_from_db()
        print(f"🔄 ON_LOADED 完成 - 加载了 {len(self.clipboard_items)} 条记录")
        
    def setup_ui(self):
        """设置用户界面"""
        self.setMinimumSize(320, 200)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 12px;
                border: none;
            }
        """)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # 头部布局
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(8)
        
        # 标题
        title_label = QtWidgets.QLabel("历史剪切板")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        
        # 清空按钮
        self.clear_button = QtWidgets.QPushButton()
        self.clear_button.setIcon(qtawesome.icon('fa.trash', color='#666'))
        self.clear_button.setFixedSize(28, 28)
        self.clear_button.setToolTip("清空所有历史")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 14px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        
        # 连接清空功能
        self.clear_button.clicked.connect(self.clear_all_history)
        header_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(header_layout)
        
        # 状态标签
        self.status_label = QtWidgets.QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                background: transparent;
                padding: 4px 0px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # 滚动区域
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f5f5f5;
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c4c4c4, stop:0.5 #b8b8b8, stop:1 #c4c4c4);
                border-radius: 5px;
                min-height: 25px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #45a049, stop:1 #4CAF50);
            }
            QScrollBar::handle:vertical:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #357a38, stop:0.5 #2e7d32, stop:1 #357a38);
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #f5f5f5;
                height: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c4c4c4, stop:0.5 #b8b8b8, stop:1 #c4c4c4);
                border-radius: 5px;
                min-width: 25px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:0.5 #45a049, stop:1 #4CAF50);
            }
            QScrollBar::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357a38, stop:0.5 #2e7d32, stop:1 #357a38);
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
            }
        """)
        
        # 列表容器
        self.list_widget = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()  # 添加弹性空间
        
        self.scroll_area.setWidget(self.list_widget)
        
        # 连接滚动条事件
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.valueChanged.connect(self.on_scroll_changed)
        
        main_layout.addWidget(self.scroll_area, 1)
        
        # 添加键盘快捷键用于强制清空
        self.setFocusPolicy(Qt.StrongFocus)  # 允许接收键盘事件
        
        # 更新状态
        self.update_status()
        
    def setup_clipboard_listener(self):
        """设置剪切板监听"""
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_changed)

    def force_create_table(self):
        """强制创建数据库表"""
        try:
            if hasattr(self, 'context') and self.context.db_config:
                # 获取表名和数据库连接
                table_name = self.context.db_config.table.name
                db = self.context.db_config._db
                
                # 先删除旧表（如果存在）
                try:
                    db.query(f'DROP TABLE IF EXISTS "{table_name}"')
                    print(f"删除旧表: {table_name}")
                except Exception as drop_e:
                    print(f"删除旧表时出错（忽略）: {drop_e}")
                
                # 使用更简单的表结构，避免约束导致的问题
                create_table_sql = f'''
                CREATE TABLE "{table_name}" (
                    id TEXT,
                    content TEXT,
                    timestamp TEXT,
                    type TEXT
                )
                '''
                
                # 执行创建表的SQL
                db.query(create_table_sql)
                print(f"强制创建表成功: {table_name}")
                
                # 重新获取表引用
                self.context.db_config.table = db[table_name]
                
                # 测试表是否可用，使用更简单的测试数据
                test_data = {
                    'id': 'test',
                    'content': 'test',
                    'timestamp': '2025-01-01T00:00:00',
                    'type': 'text'
                }
                
                try:
                    self.context.db_config.table.insert(test_data)
                    self.context.db_config.table.delete(id='test')
                    print(f"表 {table_name} 测试通过")
                except Exception as test_e:
                    print(f"表测试失败: {test_e}")
                    # 如果测试失败，清空表再试一次
                    try:
                        db.query(f'DELETE FROM "{table_name}"')
                        print("清空表后重新测试...")
                        self.context.db_config.table.insert(test_data)
                        self.context.db_config.table.delete(id='test')
                        print("清空表后测试通过")
                    except Exception as retry_e:
                        print(f"清空表后测试仍失败: {retry_e}")
                        raise retry_e
                
        except Exception as e:
            print(f"强制创建表失败: {e}")
            # 如果还是失败，尝试使用更简单的方式
            try:
                print("尝试创建最简单的表结构...")
                if hasattr(self, 'context') and self.context.db_config:
                    table_name = self.context.db_config.table.name
                    db = self.context.db_config._db
                    
                    # 删除表
                    try:
                        db.query(f'DROP TABLE IF EXISTS "{table_name}"')
                    except:
                        pass
                    
                    # 创建最简单的表
                    simple_sql = f'CREATE TABLE "{table_name}" (id, content, timestamp, type)'
                    db.query(simple_sql)
                    
                    # 重新获取表引用
                    self.context.db_config.table = db[table_name]
                    print("创建最简单表结构成功")
                    
            except Exception as simple_e:
                print(f"创建最简单表结构也失败: {simple_e}")
                # 最后的备用方案：让dataset自动创建
                print("使用dataset自动创建作为最后的备用方案...")
    
    def on_clipboard_changed(self):
        """处理剪切板内容变化"""
        try:
            # 如果剪切板被阻塞（我们正在复制），不处理
            if self.clipboard.signalsBlocked():
                print("剪切板信号被阻塞，跳过处理")
                return
                
            mime_data = self.clipboard.mimeData()
            if mime_data.hasText():
                content = mime_data.text()
                print(f"检测到剪切板变化: {content[:50]}...")
                
                # 检查内容是否为空或与上次相同（去重）
                if content and content != self.last_clipboard_content:
                    # 添加额外的长度检查，过滤掉过长的内容（可能是误操作）
                    if len(content) <= 10000:  # 限制最大长度为10KB
                        self.last_clipboard_content = content
                        self.add_clipboard_item(content)
                        print(f"添加到历史记录: {content[:30]}...")
                    else:
                        print(f"内容过长 ({len(content)} 字符)，跳过")
                else:
                    print("内容为空或与上次相同，跳过")
            else:
                print("剪切板不包含文本内容")
        except Exception as e:
            print(f"处理剪切板变化时出错: {e}")
    
    def add_clipboard_item(self, content):
        """添加新的剪切板项目"""
        # 检查是否已存在相同内容（在最近的几条记录中）
        for item in self.clipboard_items[:5]:  # 只检查最近5条
            if item['content'] == content:
                return  # 如果最近已有相同内容，不重复添加

        # 创建新项目
        item_data = {
            'id': str(uuid.uuid4()),
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'type': 'text'
        }
        
        # 插入到列表开头
        self.clipboard_items.insert(0, item_data)
        
        # 限制历史记录数量（最多保存1000条）
        if len(self.clipboard_items) > 1000:
            self.clipboard_items = self.clipboard_items[:1000]
        
        # 保存到数据库
        self.save_item_to_db(item_data)
        
        # 如果是第一页，立即显示新项目
        if self.current_page > 0:
            # 创建新项目的UI组件
            new_item_widget = self.create_item_widget(item_data)
            
            # 插入到列表顶部
            self.list_layout.insertWidget(0, new_item_widget)
            
            print(f"添加新剪切板项目: {content[:50]}...")
        else:
            # 如果还没有加载任何页面，刷新显示
            self.refresh_current_page()
        
        # 更新状态
        self.update_status()
        
    def create_item_widget(self, item_data):
        """创建剪切板项目UI组件"""
        item_widget = ClipboardItemWidget(
            item_data['id'], 
            item_data['content'], 
            item_data['timestamp']
        )
        
        # 连接信号
        item_widget.item_clicked.connect(self.on_item_clicked)
        item_widget.item_deleted.connect(self.delete_item)
        
        return item_widget
    
    def on_item_clicked(self, content):
        """处理项目双击事件，复制内容到剪切板"""
        try:
            # 临时禁用监听器，避免循环
            self.clipboard.blockSignals(True)
            self.clipboard.setText(content)
            self.clipboard.blockSignals(False)
            
            # 更新最后的剪切板内容
            self.last_clipboard_content = content
            
            # 显示复制成功的视觉反馈
            self.show_copy_feedback()
            
        except Exception as e:
            print(f"复制到剪切板时出错: {e}")
    
    def show_copy_feedback(self):
        """显示复制成功的反馈"""
        # 临时更改状态标签
        original_text = self.status_label.text()
        self.status_label.setText("✅ 已成功复制到剪切板！")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #4CAF50;
                background: transparent;
                padding: 4px 0px;
                font-weight: bold;
            }
        """)
        
        # 2秒后恢复
        QTimer.singleShot(2000, lambda: (
            self.status_label.setText(original_text),
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #666;
                    background: transparent;
                    padding: 4px 0px;
                }
            """)
        ))
    
    def delete_item(self, item_id):
        """删除指定的剪切板项目"""
        # 从数据列表中移除
        self.clipboard_items = [item for item in self.clipboard_items if item['id'] != item_id]
        
        # 从数据库中删除
        self.delete_item_from_db(item_id)
        
        # 刷新显示
        self.refresh_current_page()
        
        # 更新状态
        self.update_status()
        
    def clear_all_history(self):
        """清空所有历史记录 - 带确认对话框版本"""
        try:
            # 检查是否有数据需要清空
            print(f"🔍 检查数据数量: {len(self.clipboard_items)} 条记录")
            if len(self.clipboard_items) == 0:
                QtWidgets.QMessageBox.information(
                    None, '提示',
                    '当前没有历史记录需要清空。',
                    QtWidgets.QMessageBox.Ok
                )
                print("⚠️ 没有历史记录需要清空")
                return
            
            # 显示确认对话框
            print(f"💬 显示确认对话框，准备清空 {len(self.clipboard_items)} 条记录")
            reply = QtWidgets.QMessageBox.question(
                None, '确认清空',
                f'确定要清空所有 {len(self.clipboard_items)} 条剪切板历史吗？\n\n此操作无法撤销。',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            print(f"📋 用户选择: {'确认' if reply == QtWidgets.QMessageBox.Yes else '取消'}")
            
            # 如果用户确认，执行清空操作
            if reply == QtWidgets.QMessageBox.Yes:
                print("✅ 开始执行清空操作...")
                old_count = len(self.clipboard_items)
                
                # 清空数据库
                print("🗃️ 正在清空数据库...")
                self.clear_db()
                
                # 清空内存数据
                print("💾 正在清空内存数据...")
                self.clipboard_items.clear()
                self.current_page = 0
                
                # 清空UI
                print("🎨 正在清空UI...")
                self.clear_list_ui()
                
                # 更新状态
                print("📊 正在更新状态...")
                self.update_status()
                
                print(f"✅ 清空操作完成！已清空 {old_count} 条历史记录")
                
                # 显示完成提示
                QtWidgets.QMessageBox.information(
                    self, '清空完成', 
                    f'已成功清空 {old_count} 条历史记录。',
                    QtWidgets.QMessageBox.Ok
                )
            else:
                print("❌ 用户取消了清空操作")
                
        except Exception as e:
            print(f"❌ 清空历史记录时出错: {e}")
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, '错误', 
                f'清空历史记录时出错：\n{str(e)}',
                QtWidgets.QMessageBox.Ok
            )
    
    def on_scroll_changed(self, value):
        """处理滚动条变化，实现懒加载"""
        scrollbar = self.scroll_area.verticalScrollBar()
        # 当滚动到底部附近时加载更多
        if scrollbar.maximum() > 0 and value >= scrollbar.maximum() - 10:
            # 检查是否还有更多数据可以加载
            if self.current_page * self.page_size < len(self.clipboard_items):
                self.load_more_items()
                print("滚动到底部，加载更多数据")
    
    def load_more_items(self):
        """加载更多项目"""
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, len(self.clipboard_items))
        
        if start_index < len(self.clipboard_items):
            # 添加新页面的项目
            for i in range(start_index, end_index):
                item_data = self.clipboard_items[i]
                item_widget = self.create_item_widget(item_data)
                
                # 添加到布局（在弹性空间之前）
                self.list_layout.insertWidget(self.list_layout.count() - 1, item_widget)
            
            self.current_page += 1
            self.update_status()
            print(f"加载了第 {self.current_page} 页，显示 {start_index} 到 {end_index-1} 条记录")
    
    def refresh_current_page(self):
        """刷新当前页面显示"""
        # 清空当前UI
        self.clear_list_ui()
        
        # 重新加载第一页
        self.current_page = 0
        self.load_more_items()
        print(f"刷新显示，总共有 {len(self.clipboard_items)} 条历史记录")
    
    def clear_list_ui(self):
        """清空列表UI"""
        try:
            print(f"🧹 开始清空UI...")
            print(f"📊 清空UI前，布局中有 {self.list_layout.count()} 个组件")
            
            # 先列出所有组件
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item:
                    if item.widget():
                        widget_type = type(item.widget()).__name__
                        print(f"  - 组件 {i}: {widget_type}")
                    elif item.layout():
                        print(f"  - 组件 {i}: Layout")
                    else:
                        print(f"  - 组件 {i}: Spacer")
            
            removed_count = 0
            items_to_remove = []
            
            # 收集需要删除的组件（除了最后的弹性空间）
            for i in range(self.list_layout.count() - 1):
                items_to_remove.append(i)
            
            print(f"📝 准备删除 {len(items_to_remove)} 个组件")
            
            # 从后往前删除，避免索引问题
            for i in reversed(items_to_remove):
                child = self.list_layout.takeAt(i)
                if child:
                    if child.widget():
                        widget = child.widget()
                        widget_type = type(widget).__name__
                        print(f"  🗑️ 删除组件: {widget_type}")
                        widget.setParent(None)
                        widget.deleteLater()
                        removed_count += 1
                    elif child.layout():
                        print(f"  🗑️ 删除布局")
                        child.layout().setParent(None)
                        child.layout().deleteLater()
                        removed_count += 1
            
            print(f"✅ UI清空完成，移除了 {removed_count} 个组件")
            print(f"📊 清空UI后，布局中还有 {self.list_layout.count()} 个组件")
            
            # 强制刷新UI
            self.list_widget.update()
            self.scroll_area.update()
            self.update()
            
        except Exception as e:
            print(f"❌ 清空UI时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def update_status(self):
        """更新状态标签"""
        total_count = len(self.clipboard_items)
        displayed_count = min((self.current_page + 1) * self.page_size, total_count)
        
        if total_count == 0:
            status_text = "暂无剪切板历史 • 开始复制内容后将在此显示"
            self.status_label.setText(status_text)
            print(f"📊 状态更新: {status_text}")
        else:
            status_text = f"显示 {displayed_count}/{total_count} 条记录 • 双击复制到剪切板"
            self.status_label.setText(status_text)
            print(f"📊 状态更新: {status_text}")
    
    # 数据库操作方法
    def save_item_to_db(self, item_data):
        """保存项目到数据库"""
        # 如果数据库功能被禁用，直接返回
        if self.db_disabled:
            return
            
        try:
            if hasattr(self, 'context') and self.context.db_config:
                # 确保所有字段都是字符串类型，并进行额外的数据清理
                safe_data = {
                    'id': str(item_data['id']).strip(),
                    'content': str(item_data['content']).strip(),
                    'timestamp': str(item_data['timestamp']).strip(),
                    'type': str(item_data.get('type', 'text')).strip()
                }
                
                # 额外的数据验证
                if not safe_data['id'] or not safe_data['content']:
                    print("数据验证失败：ID或内容为空")
                    return
                
                # 限制内容长度，避免过长的内容导致问题
                if len(safe_data['content']) > 50000:  # 50KB限制
                    safe_data['content'] = safe_data['content'][:50000] + "...[内容过长已截断]"
                
                self.context.db_config.table.insert(safe_data)
                
        except Exception as e:
            print(f"保存到数据库时出错: {e}")
            error_str = str(e).lower()
            
            # 如果是数据库相关错误，尝试修复
            if any(keyword in error_str for keyword in [
                "no such table", "datatype mismatch", "integrityerror", 
                "operationalerror", "databaseerror", "constraint"
            ]):
                print("检测到数据库问题，尝试修复...")
                
                # 方法1：先尝试清空表
                try:
                    if hasattr(self, 'context') and self.context.db_config:
                        table_name = self.context.db_config.table.name
                        db = self.context.db_config._db
                        db.query(f'DELETE FROM "{table_name}"')
                        print("清空表成功，重试保存...")
                        
                        safe_data = {
                            'id': str(item_data['id']).strip(),
                            'content': str(item_data['content']).strip()[:1000],  # 限制为1000字符
                            'timestamp': str(item_data['timestamp']).strip(),
                            'type': 'text'  # 固定为text
                        }
                        
                        self.context.db_config.table.insert(safe_data)
                        print("清空表后保存成功")
                        return
                        
                except Exception as clear_e:
                    print(f"清空表后保存失败: {clear_e}")
                
                # 方法2：重建表
                print("尝试重建数据库表...")
                self.force_create_table()
                
                # 重试保存，使用更保守的数据
                try:
                    safe_data = {
                        'id': str(item_data['id'])[:50],  # 限制ID长度
                        'content': str(item_data['content'])[:1000],  # 限制内容长度
                        'timestamp': str(item_data['timestamp'])[:30],  # 限制时间戳长度
                        'type': 'text'
                    }
                    
                    # 确保没有特殊字符
                    for key, value in safe_data.items():
                        safe_data[key] = value.replace('\x00', '').replace('\r', ' ').replace('\n', ' ')
                    
                    self.context.db_config.table.insert(safe_data)
                    print("重建表后保存成功")
                    
                except Exception as retry_e:
                    print(f"重建表后保存仍然失败: {retry_e}")
                    self.db_error_count += 1
                    # 如果连续失败太多次，暂时禁用数据库功能
                    if self.db_error_count >= 5:
                        self.db_disabled = True
                        print("⚠️ 数据库错误过多，暂时禁用数据保存功能")
                        print("剪切板监听继续工作，但历史记录不会保存到数据库")
                    else:
                        print(f"放弃保存这条记录，继续运行... (错误计数: {self.db_error_count}/5)")
            else:
                print(f"非数据库错误，跳过修复: {e}")
                self.db_error_count += 1
    
    def delete_item_from_db(self, item_id):
        """从数据库删除项目"""
        try:
            if hasattr(self, 'context') and self.context.db_config:
                # 确保ID是字符串类型
                self.context.db_config.table.delete(id=str(item_id))
        except Exception as e:
            print(f"从数据库删除时出错: {e}")
    
    def clear_db(self):
        """清空数据库"""
        try:
            if hasattr(self, 'context') and self.context.db_config:
                # 方法1：使用dataset的delete方法
                try:
                    self.context.db_config.table.delete()
                    print("✅ 使用dataset.delete()清空数据库成功")
                    return
                except Exception as delete_e:
                    print(f"dataset.delete()失败: {delete_e}")
                
                # 方法2：使用SQL DELETE语句
                try:
                    table_name = self.context.db_config.table.name
                    db = self.context.db_config._db
                    db.query(f'DELETE FROM "{table_name}"')
                    print("✅ 使用SQL DELETE清空数据库成功")
                    return
                except Exception as sql_e:
                    print(f"SQL DELETE失败: {sql_e}")
                
                # 方法3：删除并重建表
                try:
                    print("尝试删除并重建表...")
                    self.force_create_table()
                    print("✅ 重建表成功")
                    return
                except Exception as rebuild_e:
                    print(f"重建表失败: {rebuild_e}")
                
                print("⚠️ 所有数据库清空方法都失败了")
            else:
                print("⚠️ 数据库配置不可用，跳过数据库清空")
                
        except Exception as e:
            print(f"❌ 清空数据库时出错: {e}")
            # 即使数据库清空失败，也不阻止UI清空
    
    def rebuild_database_table(self):
        """重建数据库表，解决数据类型不匹配问题"""
        print("重建数据库表...")
        self.force_create_table()
    
    def load_history_from_db(self):
        """从数据库加载历史记录"""
        try:
            if hasattr(self, 'context') and self.context.db_config:
                # 按时间戳降序排列（最新的在前面）
                records = list(self.context.db_config.table.all())
                
                # 确保数据格式正确，并按时间戳排序
                processed_records = []
                for record in records:
                    # 确保每个记录都有必要的字段
                    processed_record = {
                        'id': str(record.get('id', '')),
                        'content': str(record.get('content', '')),
                        'timestamp': str(record.get('timestamp', '')),
                        'type': str(record.get('type', 'text'))
                    }
                    # 只添加有效的记录
                    if processed_record['id'] and processed_record['content']:
                        processed_records.append(processed_record)
                
                # 按时间戳排序
                processed_records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                self.clipboard_items = processed_records
                
                print(f"从数据库加载了 {len(self.clipboard_items)} 条历史记录")
                
                # 加载第一页
                if self.clipboard_items:
                    self.load_more_items()
                else:
                    print("没有找到历史记录")
                    
                self.update_status()
        except Exception as e:
            print(f"从数据库加载时出错: {e}")
            # 如果加载失败，可能是数据库结构问题，尝试重建
            if "no such column" in str(e).lower() or "datatype" in str(e).lower():
                print("检测到数据库结构问题，尝试重建...")
                self.rebuild_database_table()
                # 重建后清空内存中的数据
                self.clipboard_items = []
                self.update_status()

    def get_config(self):
        """获取配置信息（主要用于保存组件状态）"""
        return {}

    def set_config(self, config):
        """设置配置信息"""
        pass


if __name__ == '__main__':
    import sys
    from fingertips.db_utils import ConfigDB
    
    app = QtWidgets.QApplication(sys.argv)

    # 创建主窗口
    window = HistoricalCuttingBoardCard()
    
    # 为测试创建模拟的context对象
    class MockContext:
        def __init__(self):
            self.wid = 'test_widget'
            self.db_config = ConfigDB('HistoricalCuttingBoardCard_Test')
    
    window.context = MockContext()
    
    window.show()
    sys.exit(app.exec_()) 