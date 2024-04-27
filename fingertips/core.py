import openai
import markdown2
from PySide2 import QtCore
from pygments.formatters import HtmlFormatter

from fingertips.settings import OPENAI_INFO
from fingertips.utils import get_logger


log = get_logger('core')


class AskAIThread(QtCore.QThread):
    resulted = QtCore.Signal(str)

    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.question = question
        self.openai_client = openai.OpenAI(
            api_key=OPENAI_INFO['api_key'],
            base_url=OPENAI_INFO['url']
        )
        self.markdown_parser = markdown2.Markdown(
            extras=["fenced-code-blocks", "code-friendly", "cuddled-lists"]
        )

        formatter = HtmlFormatter(style='monokai')
        self.pygments_css = formatter.get_style_defs('.codehilite')

    def run(self):
        self.resulted.emit(self.default_message())

        log.info('starting ask ai....')
        response = self.openai_client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{
                'role': 'user',
                'content': self.question
            }],
            stream=True
        )

        log.info('waiting response...')
        res_test = ''
        try:
            for chunk in response:
                if not chunk.choices:
                    continue

                if chunk.choices[0].delta.content is not None:
                    res_test += chunk.choices[0].delta.content
                    self.resulted.emit(
                        self.generate_style(
                            self.markdown_parser.convert(res_test.strip())
                        ))
        except Exception as e:
            self.resulted.emit(
                self.generate_style(
                    self.markdown_parser.convert(f'```{str(e)}```')
                ))

    @staticmethod
    def default_message():
        return '''<body style="color:white;background-color:#303133;
            font-size: 14px;padding: 0 4px;box-sizing: border-box;">
        思考中，请稍后...
        </body>'''

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
