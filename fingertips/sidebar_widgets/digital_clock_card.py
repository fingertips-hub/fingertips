import sys
import hashlib
import requests
from datetime import datetime
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QStackedWidget, QLineEdit, QPushButton, QFormLayout, QSizePolicy
from PySide2.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QThread, Signal
from PySide2.QtGui import QFont
from fingertips.super_sidebar.sidebar_widget_utils import SidebarWidget
import qfluentwidgets

PROXIES = {"http": None, "https": None}


class WeatherThread(QThread):
    """天气数据获取线程"""
    weather_updated = Signal(dict)
    
    def __init__(self, token, secret_key):
        super().__init__()
        self.token = token
        self.secret_key = secret_key
    
    def run(self):
        try:
            city_info = self.get_current_city()
            weather_data = self.get_weather(city_info)
            self.weather_updated.emit(weather_data)
        except Exception as e:
            print(f"获取天气数据失败: {e}")
            # 发送默认天气数据
            default_weather = {
                'city': '未知城市',
                'temperature': '--',
                'weather': '获取中...',
                'wind_direction': '--',
                'wind_speed': '--',
                'humidity': '--',
                'icon': 'unknown'
            }
            self.weather_updated.emit(default_weather)
    
    @staticmethod
    def get_current_city():
        url = 'https://qifu-api.baidubce.com/ip/local/geo/v1/district'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        }
        res = requests.get(url, headers=headers, proxies=PROXIES, timeout=5)
        data = res.json()
        data = {'code': 'Success',
         'data': {'continent': '亚洲', 'country': '中国', 'zipcode': '310051', 'owner': '中国移动',
                  'isp': '中国移动', 'adcode': '330108', 'prov': '浙江省', 'city': '杭州市',
                  'district': '滨江区'}, 'ip': '117.147.90.182'}

        # todo 缓存这个数据，每1小时更新一次
        return data['data']
    
    def get_weather(self, city_info):
        url = f'/ws/weather/v1?adcode={city_info["adcode"]}&key={self.token}'
        md5 = hashlib.md5((url + self.secret_key).encode('utf-8')).hexdigest()
        res = requests.get(
            'https://apis.map.qq.com' + url + f'&sig={md5}',
            headers={'x-legacy-url-decode': 'no'},
            timeout=5
        )
        data = res.json()
        print(data)
        result = data.get('result')

        if not result:
            print("获取天气数据失败，返回结果为空")
            return {
                'city': city_info.get('city', '未知城市'),
                'temperature': '--',
                'weather': '获取中...',
                'wind_direction': '--',
                'wind_speed': '--',
                'humidity': '--'
            }
        realtime = result['realtime'][0]
        infos = realtime['infos']
        
        # 解析天气数据
        weather_data = {
            'city': f'{realtime["city"]}-{realtime["district"]}',
            'temperature': f"{infos['temperature']}°",
            'weather': infos['weather'],
            'wind_direction': infos.get('wind_direction', '--'),
            'wind_speed': f"{infos.get('wind_power', '--')}",
            'humidity': f"{infos.get('humidity', '--')}%"
        }
        return weather_data


class DigitalClockCard(SidebarWidget):
    """美观优雅简约的数字时钟组件"""
    name = '时钟'
    category = '生活'

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # 设置最小尺寸，允许组件自适应调整
        self.setMinimumWidth(400)
        self.setMinimumHeight(130)
        self.resize(400, 130)
        # 设置大小策略，允许组件在两个方向上扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 设置窗口属性以确保正确的重绘
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        # 初始化配置
        self.token = ''
        self.secret_key = ''

        # 初始化天气数据
        self.weather_data = {
            'city': '获取中...',
            'temperature': '--',
            'weather': '获取中...',
            'wind_direction': '--',
            'wind_speed': '--',
            'humidity': '--',
            'icon': 'unknown'
        }
        
        # 初始化UI（使用双页面结构）
        self.setup_ui()
        
        # 创建定时器，每秒更新时间
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每1000毫秒（1秒）更新一次
        
        # 创建天气更新定时器，每30分钟更新一次天气
        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self.update_weather)
        self.weather_timer.start(30 * 60 * 1000)  # 30分钟
        
        # 初始化时间显示
        self.update_time()
        
        # 初始化天气数据获取
        self.update_weather()

        # 添加淡入动画效果
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(1000)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)

    def get_config(self):
        return {
            'token': self.token,
            'secret_key': self.secret_key
        }

    def set_config(self, config):
        self.token = config.get('token', '')
        self.secret_key = config.get('secret_key', '')
        self.update_weather()  # 更新天气数据

    def edit_mode_changed(self, edit_mode):
        super().edit_mode_changed(edit_mode)
        print(f"编辑模式变更: {edit_mode}")

        width, height = self.size().width(), self.size().height()
        
        # 根据编辑模式切换页面
        if edit_mode:
            self.stacked_widget.setCurrentIndex(1)  # 显示配置页面

            # 更新配置页面的输入框值
            self.token_input.setText(self.token)
            self.secret_key_input.setText(self.secret_key)
        else:
            self.save_config()
            self.stacked_widget.setCurrentIndex(0)  # 显示主页面

        widget = self.stacked_widget.currentWidget()
        widget.resize(width, height)

    def setup_ui(self):
        """设置用户界面"""
        # 创建堆叠窗口管理器
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet('border-radius: "8px"')
        
        # 创建主显示页面
        self.main_page = self.create_main_page()
        self.stacked_widget.addWidget(self.main_page)
        
        # 创建配置页面
        self.config_page = self.create_config_page()
        self.stacked_widget.addWidget(self.config_page)
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)
        
        # 默认显示主页面
        self.stacked_widget.setCurrentIndex(0)
        
    def create_main_page(self):
        """创建主显示页面（时间和天气）"""
        page = QWidget()
        
        # 创建主布局（水平布局）
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 10, 20, 20)  # 恢复合适的边距
        main_layout.setSpacing(22)
        
        # 创建一个容器来实现居中布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 左侧时间区域
        time_frame = QFrame()
        time_layout = QVBoxLayout(time_frame)
        time_layout.setContentsMargins(0, 0, 0, 0)  # 恢复正常边距
        time_layout.setSpacing(5)  # 减少间距让内容更紧凑
        
        # 时间显示标签
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
                background: transparent;
                border: none;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            }
        """)
        
        # 设置时间字体（增大字体以更突出显示）
        time_font = QFont("Segoe UI", 38, QFont.Bold)
        time_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        self.time_label.setFont(time_font)
        
        # 日期显示标签
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("""
            QLabel {
                color: #EEE;
                background: transparent;
                border: none;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
            }
        """)
        
        # 设置日期字体
        date_font = QFont("Segoe UI", 14, QFont.DemiBold)
        date_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        self.date_label.setFont(date_font)
        
        # 星期显示标签
        self.weekday_label = QLabel()
        self.weekday_label.setAlignment(Qt.AlignCenter)
        self.weekday_label.setStyleSheet("""
            QLabel {
                color: #EEE;
                background: transparent;
                border: none;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.6);
            }
        """)
        
        # 设置星期字体
        weekday_font = QFont("Segoe UI", 12, QFont.DemiBold)
        self.weekday_label.setFont(weekday_font)
        
        # 添加时间组件到时间布局 - 让时间显示在顶部区域
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.date_label)
        time_layout.addWidget(self.weekday_label)
        time_layout.addStretch()  # 底部弹性空间，将时间内容推向顶部
        
        # 右侧天气区域 - 采用卡片式设计
        weather_frame = QFrame()
        weather_main_layout = QVBoxLayout(weather_frame)
        weather_main_layout.setContentsMargins(0, 0, 0, 0)
        weather_main_layout.setSpacing(8)
        
        # 城市名称标签（顶部）
        self.city_label = QLabel()
        self.city_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.city_label.setStyleSheet("""
            QLabel {
                color: #EEE;
                background: transparent;
                border: none;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
            }
        """)
        city_font = QFont("Segoe UI", 12, QFont.Normal)  # 从9增大到11
        self.city_label.setFont(city_font)
        
        # 主要天气信息区域（图标+温度）
        main_weather_layout = QHBoxLayout()
        main_weather_layout.setSpacing(8)
        
        # 天气图标
        self.weather_icon_label = QLabel()
        self.weather_icon_label.setAlignment(Qt.AlignCenter)
        self.weather_icon_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                background: transparent;
                border: none;
            }
        """)
        icon_font = QFont("Segoe UI", 28, QFont.Normal)  # 从24增大到28
        self.weather_icon_label.setFont(icon_font)
        
        # 温度和天气描述的垂直布局
        temp_desc_layout = QVBoxLayout()
        temp_desc_layout.setSpacing(2)
        
        # 温度显示标签
        self.temperature_label = QLabel()
        self.temperature_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.temperature_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
                background: transparent;
                border: none;
                text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
            }
        """)
        temp_font = QFont("Segoe UI", 20, QFont.Bold)  # 从16增大到20
        self.temperature_label.setFont(temp_font)
        
        # 天气描述标签
        self.weather_desc_label = QLabel()
        self.weather_desc_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.weather_desc_label.setStyleSheet("""
            QLabel {
                color: #EEE;
                background: transparent;
                border: none;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
            }
        """)
        desc_font = QFont("Segoe UI", 11, QFont.Bold)  # 从8增大到10
        self.weather_desc_label.setFont(desc_font)
        
        temp_desc_layout.addWidget(self.temperature_label)
        temp_desc_layout.addWidget(self.weather_desc_label)
        
        main_weather_layout.addWidget(self.weather_icon_label)
        main_weather_layout.addLayout(temp_desc_layout)
        main_weather_layout.addStretch()
        
        # 详细信息区域（风力+湿度）- 使用网格布局
        details_layout = QHBoxLayout()
        details_layout.setSpacing(10)
        
        # 风向风力信息
        self.wind_label = QLabel()
        self.wind_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.wind_label.setStyleSheet("""
            QLabel {
                color: #EEE;
                background: transparent;
                border: none;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
            }
        """)
        wind_font = QFont("Segoe UI", 10, QFont.Normal)  # 从7增大到9
        self.wind_label.setFont(wind_font)
        
        # 湿度信息
        self.humidity_label = QLabel()
        self.humidity_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.humidity_label.setStyleSheet("""
            QLabel {
                color: #EEE;
                background: transparent;
                border: none;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
            }
        """)
        humidity_font = QFont("Segoe UI", 10, QFont.Normal)  # 从7增大到9
        self.humidity_label.setFont(humidity_font)
        
        details_layout.addWidget(self.wind_label)
        details_layout.addWidget(self.humidity_label)
        
        # 组装天气区域
        weather_main_layout.addWidget(self.city_label)
        weather_main_layout.addLayout(main_weather_layout)
        weather_main_layout.addLayout(details_layout)
        weather_main_layout.addStretch()

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("""
            QFrame {
                color: #606060;
                background-color: transparent;
                border: none;
            }
        """)
        separator.setFixedWidth(1)
        
        # 添加到内容布局
        content_layout.addWidget(time_frame)
        content_layout.addWidget(separator)
        content_layout.addWidget(weather_frame)
        
        # 将内容布局居中添加到主布局
        main_layout.addStretch()  # 左侧弹性空间
        main_layout.addLayout(content_layout)  # 居中的内容
        main_layout.addStretch()  # 右侧弹性空间
        
        page.setLayout(main_layout)
        return page
        
    def create_config_page(self):
        """创建配置页面"""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background: #ddd;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(15)

        # 配置表单
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # TOKEN输入框
        self.token_input = qfluentwidgets.LineEdit()
        self.token_input.setPlaceholderText("请输入腾讯地图API TOKEN")

        # SECRET_KEY输入框
        self.secret_key_input = qfluentwidgets.LineEdit()
        self.secret_key_input.setPlaceholderText("请输入腾讯地图API SECRET_KEY")

        token_label = qfluentwidgets.BodyLabel("TOKEN:")
        secret_label = qfluentwidgets.BodyLabel("SECRET_KEY:")
        
        # 添加到表单布局
        form_layout.addRow(token_label, self.token_input)
        form_layout.addRow(secret_label, self.secret_key_input)

        # 组装布局
        main_layout.addLayout(form_layout)
        page.setLayout(main_layout)
        return page
        
    def save_config(self):
        """保存配置并重新获取天气数据"""
        # 获取输入的配置
        new_token = self.token_input.text().strip()
        new_secret_key = self.secret_key_input.text().strip()
        
        # 验证配置不为空
        if not new_token or not new_secret_key:
            print("TOKEN和SECRET_KEY不能为空")
            return
        
        # 更新配置
        self.token = new_token
        self.secret_key = new_secret_key

        print(f"配置已保存: TOKEN={self.token[:10]}..., SECRET_KEY={self.secret_key[:10]}...")

        # 立即重新获取天气数据
        self.update_weather()
        
        # 给用户反馈
        self.weather_data['weather'] = '正在更新...'
        self.update_weather_display()
        
    def paintEvent(self, event):
        """重写绘制事件，确保透明背景正确清除"""
        # 不绘制任何背景，保持完全透明
        super().paintEvent(event)
        
    def resizeEvent(self, event):
        """重写调整大小事件，确保布局正确响应"""
        super().resizeEvent(event)
        # 确保堆叠组件也调整到正确的大小
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.resize(event.size())
        # 强制更新布局
        if self.layout():
            self.layout().update()
        
    def update_time(self):
        """更新时间显示"""
        now = datetime.now()
        
        # 格式化时间 (24小时制)
        time_str = now.strftime("%H:%M:%S")
        self.time_label.setText(time_str)
        # 强制重绘时间标签
        self.time_label.update()
        
        # 格式化日期
        date_str = now.strftime("%Y年%m月%d日")
        self.date_label.setText(date_str)
        # 强制重绘日期标签
        self.date_label.update()
        
        # 格式化星期
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_str = weekdays[now.weekday()]
        self.weekday_label.setText(weekday_str)
        # 强制重绘星期标签
        self.weekday_label.update()
        
        # 强制重绘整个组件
        self.update()

    def update_weather(self):
        """更新天气信息"""
        if not self.token or not self.secret_key:
            return

        self.weather_thread = WeatherThread(self.token, self.secret_key)
        self.weather_thread.weather_updated.connect(self.on_weather_updated)
        self.weather_thread.start()
        
    def on_weather_updated(self, weather_data):
        """天气数据更新回调"""
        self.weather_data = weather_data
        self.update_weather_display()
        
    def update_weather_display(self):
        """更新天气显示"""
        # 更新城市名称
        self.city_label.setText(self.weather_data['city'])
        
        # 更新温度
        self.temperature_label.setText(self.weather_data['temperature'])
        
        # 更新天气描述
        self.weather_desc_label.setText(self.weather_data['weather'])
        
        # 更新风向风力信息
        wind_direction = self.weather_data.get('wind_direction', '--')
        wind_speed = self.weather_data.get('wind_speed', '--')
        
        # 风向转换为简洁的中文
        wind_direction_map = {
            'N': '北', 'NE': '东北', 'E': '东', 'SE': '东南',
            'S': '南', 'SW': '西南', 'W': '西', 'NW': '西北',
            'C': '无风', '--': '--'
        }
        wind_direction_cn = wind_direction_map.get(wind_direction, wind_direction)
        
        if wind_direction != '--' and wind_speed != '--':
            # 简化显示格式
            if wind_direction_cn == '无风':
                wind_text = f"🌬 {wind_direction_cn}"
            else:
                wind_text = f"🌬 {wind_direction_cn} {wind_speed}"
        else:
            wind_text = "🌬 --"
        self.wind_label.setText(wind_text)
        
        # 更新湿度信息
        humidity = self.weather_data.get('humidity', '--')
        if humidity != '--':
            humidity_text = f"💧 {humidity}"
        else:
            humidity_text = "💧 --"
        self.humidity_label.setText(humidity_text)
        
        # 更新天气图标（使用Unicode符号）
        weather_icons = {
            '晴': '☀',
            '多云': '⛅',
            '阴': '☁',
            '雨': '🌦',
            '小雨': '🌦',
            '中雨': '🌧',
            '大雨': '⛈',
            '雷阵雨': '⛈',
            '雪': '❄',
            '雾': '🌫',
            '霾': '🌫',
            '沙尘暴': '💨',
            'unknown': '❓'
        }
        
        weather = self.weather_data['weather']
        icon = weather_icons.get(weather, weather_icons['unknown'])
        
        # 根据天气类型选择合适的图标
        for key in weather_icons:
            if key in weather:
                icon = weather_icons[key]
                break
                
        self.weather_icon_label.setText(icon)

    def show_with_animation(self):
        """显示时钟并播放淡入动画"""
        self.show()
        # 调整窗口大小以适应内容
        self.adjustSize()
        self.opacity_animation.start()


class DigitalClockApp(QApplication):
    """数字时钟应用程序"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.clock = DigitalClockCard()
        
    def run(self):
        """运行应用程序"""
        # 将时钟窗口居中显示
        screen = self.primaryScreen().geometry()
        clock_rect = self.clock.frameGeometry()
        clock_rect.moveCenter(screen.center())
        self.clock.move(clock_rect.topLeft())
        
        # 显示时钟
        self.clock.show_with_animation()
        
        return self.exec_()


def main():
    """主函数"""
    app = DigitalClockApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main() 