import os

import qfluentwidgets
from fingertips.config import CONFIG_ROOT


class UrlValidator(qfluentwidgets.ConfigValidator):
    def validate(self, value):
        return value.startswith(('http://', 'https://'))


class Config(qfluentwidgets.QConfig):
    main_window_shortcut = qfluentwidgets.ConfigItem('shortcut', 'main_window', 'ctrl+`')
    chat_window_shortcut = qfluentwidgets.ConfigItem('shortcut', 'chat_window', 'F10')
    action_menu_shortcut = qfluentwidgets.ConfigItem('shortcut', 'action_menu', 'F8')
    ai_resend_shortcut = qfluentwidgets.ConfigItem('shortcut', 'ai_resend_shortcut', 'F7')

    openai_base = qfluentwidgets.ConfigItem(
        'openai', 'base', 'https://api.openai.com/v1', UrlValidator())
    openai_key = qfluentwidgets.ConfigItem('openai', 'key', '')
    openai_models = qfluentwidgets.ConfigItem('openai', 'models', ['gpt-4o', 'gpt-3.5-turbo'])
    openai_current_model = qfluentwidgets.ConfigItem('openai', 'current_model', 'gpt-3.5-turbo')
    openai_temperature = qfluentwidgets.RangeConfigItem(
        'openai', 'temperature', 0.6, qfluentwidgets.RangeValidator(0, 2))

    coze_user_id = qfluentwidgets.ConfigItem('coze', 'user_id', '')
    coze_key = qfluentwidgets.ConfigItem('coze', 'key', '')

    chat_pin = qfluentwidgets.ConfigItem('chat', 'pin', True)

    enable_super_sidebar = qfluentwidgets.ConfigItem(
        'super_sidebar', 'enable', False, qfluentwidgets.BoolValidator())
    super_sidebar_type = qfluentwidgets.OptionsConfigItem(
      'super_sidebar', 'type', 'acrylic', qfluentwidgets.OptionsValidator(['acrylic', 'translucent']))
    super_sidebar_opacity = qfluentwidgets.RangeConfigItem(
        'super_sidebar', 'opacity', 0.6, qfluentwidgets.RangeValidator(0, 1))
    super_sidebar_width = qfluentwidgets.RangeConfigItem(
       'super_sidebar', 'width', 500, qfluentwidgets.RangeValidator(400, 800))
    super_sidebar_position = qfluentwidgets.OptionsConfigItem(
       'super_sidebar', 'position', 'right', qfluentwidgets.OptionsValidator(['left', 'right']))
    super_sidebar_plugin_path = qfluentwidgets.ConfigItem(
      'super_sidebar', 'plugin_path', f'{CONFIG_ROOT}/plugins'.replace('\\', '/'))

    update_on_start = qfluentwidgets.ConfigItem(
        'update', 'update_on_start', True, qfluentwidgets.BoolValidator())


config_model = Config()
qfluentwidgets.qconfig.load(os.path.join(CONFIG_ROOT, 'config.json'), config_model)
