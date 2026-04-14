"""⑦ Windows 탐색기 재시작"""

import time
from tools.base import BaseTool


class ExplorerRestartTool(BaseTool):
    tool_id = "explorer_restart"
    name = "Windows 탐색기 재시작"
    requires_admin = False
    requires_reboot = False

    def get_steps(self):
        return ["탐색기 종료", "탐색기 재시작"]

    def run(self, log):
        self._run_cmd("taskkill /F /IM explorer.exe", log)
        log("탐색기 종료 완료", 0)

        time.sleep(1)
        self._run_cmd("start explorer.exe", log)
        log("탐색기 재시작 완료. 화면이 잠시 깜빡일 수 있습니다.", 1)
        return True
