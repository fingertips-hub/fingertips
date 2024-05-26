import openai
import markdown2
from PySide2 import QtCore
from pygments.formatters import HtmlFormatter

from fingertips.utils import get_logger
from fingertips.settings.config_model import config_model

log = get_logger('core')


class AskAIThread(QtCore.QThread):
    resulted = QtCore.Signal(str)
    finished = QtCore.Signal(str)

    def __init__(self, question, model='', temperature=None, max_tokens=0, system_prompt='',
                 convert_markdown=True, histories=None, parent=None):
        super().__init__(parent)
        self.question = system_prompt.replace('{{TEXT}}', question) or question
        self.model = model or config_model.openai_current_model.value
        self.temperature = temperature or config_model.openai_temperature.value
        self.max_tokens = max_tokens or openai.NotGiven()
        self.convert_markdown = convert_markdown
        self.histories = histories

        self.openai_client = openai.OpenAI(
            api_key=config_model.openai_key.value,
            base_url=config_model.openai_base.value
        )
        self.markdown_parser = markdown2.Markdown(
            extras=["fenced-code-blocks", "code-friendly", "cuddled-lists"]
        )

        formatter = HtmlFormatter(style='monokai')
        self.pygments_css = formatter.get_style_defs('.codehilite')

    def run(self):
        self.resulted.emit(self.default_message())

        log.info('starting ask ai....')
        try:
            messages = [{
                    'role': 'user',
                    'content': self.question
                }]
            if self.histories:
                messages = [*self.histories, *messages]

            response = self.openai_client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=messages,
                stream=True
            )

            log.info('waiting response...')
            res_test = ''
            for chunk in response:
                if not self.isInterruptionRequested():
                    if not chunk.choices:
                        continue

                    if chunk.choices[0].delta.content is not None:
                        res_test += chunk.choices[0].delta.content
                        if self.convert_markdown:
                            data = self.generate_style(
                                self.markdown_parser.convert(res_test)
                            )
                            self.resulted.emit(data)
                        else:
                            self.resulted.emit(res_test)

        except Exception as e:
            if self.convert_markdown:
                res_test = f'请求错误：```{str(e)}```'
                self.resulted.emit(
                    self.generate_style(self.markdown_parser.convert(res_test))
                )
            else:
                res_test = f'请求错误：{str(e)}'
                self.resulted.emit(res_test)

        self.finished.emit(res_test.strip())

    def default_message(self):
        if self.convert_markdown:
            return '''<body style="color:white;background-color:#303133;
                font-size: 14px;padding: 0 4px;box-sizing: border-box;">
            思考中，请稍后...
            </body>'''
        else:
            return '思考中，请稍后...'

    def generate_style(self, html_content):
        return f"""
        <html>
        <head>
        <meta charset="UTF-8">
        <title>Document</title>
        <style> {self.pygments_css} </style>
        <style>.codehilite {{padding: 6px;box-sizing: border-box;border-radius: 6px; }}</style>
        <style>code{{padding: 4px; margin: 0 2px; background-color: #272822;box-sizing: border-box;border-radius: 2px}}</style>
        <style>
        ::-webkit-scrollbar {{
            width: 8px; /* 设置滚动条的宽度 */
        }}
        /* 滚动条轨道 */
        ::-webkit-scrollbar-track {{
            background: #303133; /* 轨道的背景颜色 */
        }}
        /* 滚动条滑块 */
        ::-webkit-scrollbar-thumb {{
            background: #444; /* 滑块的背景颜色 */
        }}
        /* 滚动条按钮（可选，不是所有浏览器都支持） */
        ::-webkit-scrollbar-button {{
            display: block;
            height: 0;
            background-color: #303133;
        }}
        </style>
        </head> 
        <body style="background-color: #303133;color: white; font-size:14px; padding: 0 4px;box-sizing: border-box;overflow-x: hidden;line-height:22px;">{html_content}</body> 
        </html> """
