"""⑪ 원격 지원 접속"""

import webbrowser
from tools.base import BaseTool
import config


class RemoteSupportTool(BaseTool):
    tool_id = "remote_support"
    name = "원격 지원 접속"
    requires_admin = False
    requires_reboot = False

    def get_steps(self):
        return ["원격 지원 페이지 열기"]

    def run(self, log):
        url = config.REMOTE_SUPPORT_URL
        webbrowser.open(url)
        log(f"원격 지원 페이지를 열었습니다: {url}", 0)
        return True
