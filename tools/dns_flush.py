"""④ DNS 캐시 초기화"""

from tools.base import BaseTool


class DnsFlushTool(BaseTool):
    tool_id = "dns_flush"
    name = "DNS 캐시 초기화"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return ["DNS 캐시 플러시", "DNS 재등록"]

    def run(self, log):
        self._run_cmd("ipconfig /flushdns", log)
        log("DNS 캐시 플러시 완료", 0)

        self._run_cmd("ipconfig /registerdns", log)
        log("DNS 재등록 완료", 1)
        return True
