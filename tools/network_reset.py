"""⑤ 네트워크 초기화"""

from tools.base import BaseTool


class NetworkResetTool(BaseTool):
    tool_id = "network_reset"
    name = "네트워크 초기화"
    requires_admin = True
    requires_reboot = True

    def get_steps(self):
        return ["Winsock 리셋", "TCP/IP 리셋", "DNS 캐시 플러시"]

    def run(self, log):
        self._run_cmd("netsh winsock reset", log)
        log("Winsock 리셋 완료", 0)

        self._run_cmd("netsh int ip reset", log)
        log("TCP/IP 리셋 완료 (고정 IP는 유지됩니다)", 1)

        self._run_cmd("ipconfig /flushdns", log)
        log("DNS 캐시 플러시 완료. 재부팅이 필요합니다.", 2)
        return True
