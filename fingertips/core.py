import openai
import markdown2
from PySide2 import QtCore
from pygments.formatters import HtmlFormatter

from fingertips.settings import OPENAI_INFO


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
        response = self.openai_client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{
                'role': 'user',
                'content': self.question
            }],
            stream=True
        )

        res_test = ''
        for chunk in response:
            if not chunk.choices:
                continue

            if chunk.choices[0].delta.content is not None:
                res_test += chunk.choices[0].delta.content
                self.resulted.emit(
                    self.generate_style(
                        self.markdown_parser.convert(res_test)
                    ))

    def generate_style(self, html_content):
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document</title>
        <style> {self.pygments_css} </style> 
        <style>.codehilite {{padding: 6px;box-sizing: border-box;border-radius: 6px; }}</style>
        <style>code{{padding: 4px; background-color: #272822;box-sizing: border-box;border-radius: 2px}}</style>
        </head> 
        <body style="background-color: #303133;color: white; font-size:14px; padding: 6px;box-sizing: border-box;">
          {html_content} 
        </body> 
        </html> """
