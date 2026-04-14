"""① 프린터 스풀링 초기화"""

import os
from tools.base import BaseTool


class PrinterSpoolerTool(BaseTool):
    tool_id = "printer_spooler"
    name = "프린터 스풀링 초기화"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return ["Spooler 서비스 정지", "대기열 삭제", "서비스 재시작"]

    def run(self, log):
        spool_dir = r"C:\Windows\System32\spool\PRINTERS"

        self._stop_service("Spooler", log)
        log("Spooler 서비스 정지 완료", 0)

        try:
            cnt = self._delete_files(spool_dir, log)
            log(f"대기열 파일 {cnt}개 삭제", 1)
        except Exception as e:
            log(f"대기열 삭제 오류: {e}", -1)

        self._start_service("Spooler", log)
        log("Spooler 서비스 재시작 완료", 2)
        return True
