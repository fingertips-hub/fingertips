import openai
import markdown
from PySide2 import QtCore

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

    def run(self):
        response = self.openai_client.chat.completions.create(
            model='gpt-4-all',
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
                self.resulted.emit(markdown.markdown(res_test))
