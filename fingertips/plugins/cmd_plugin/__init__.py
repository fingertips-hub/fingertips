import os

from fingertips.core import register
from fingertips.core.plugin import AbstractPlugin


@register
class CmdPlugin(AbstractPlugin):
    title = u'CMD'
    keyword = 'cmd'
    description = u'执行CMD命令'

    def run(self, text, result_item, plugin_by_keyword):
        os.system('start cmd /k {}'.format(text))


if __name__ == '__main__':
    cp = CmdPlugin()
    cp.run('ipconfig', None, None)
