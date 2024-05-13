import webbrowser

from fingertips.core import register
from fingertips.core.action import AbstractAction, TEXT


class WebSearchAction(AbstractAction):
    action_types = [TEXT]
    url_parse = ''

    def run(self, text):
        webbrowser.open(self.url_parse.format(text))


@register
class BaiduSearchAction(WebSearchAction):
    title = '百度搜索'
    description = '使用百度搜索所选关键词'
    url_parse = 'https://www.baidu.com/s?ie=UTF-8&wd={}'


@register
class GoogleSearchAction(WebSearchAction):
    title = 'google搜索'
    description = '使用Google搜索所选关键词'
    url_parse = 'https://www.google.com/search?q={}'
