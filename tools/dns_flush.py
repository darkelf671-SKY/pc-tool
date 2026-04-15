"""④ DNS·SSL·프록시 초기화"""

from tools.base import BaseTool


class DnsFlushTool(BaseTool):
    tool_id = "dns_flush"
    name = "DNS·SSL·프록시 초기화"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return ["DNS 캐시 플러시", "DNS 재등록",
                "SSL 인증서 캐시 초기화", "프록시 설정 초기화"]

    def run(self, log):
        # Step 0: DNS 캐시 플러시
        self._run_cmd("ipconfig /flushdns", log)
        log("DNS 캐시 플러시 완료", 0)

        # Step 1: DNS 재등록
        self._run_cmd("ipconfig /registerdns", log)
        log("DNS 재등록 완료", 1)

        # Step 2: SSL 인증서 캐시 초기화
        self._run_cmd("certutil -urlcache * delete", log)
        log("SSL 인증서 캐시 초기화 완료", 2)

        # Step 3: 프록시 설정 초기화
        ps = (
            'Set-ItemProperty '
            '-Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion'
            '\\Internet Settings" '
            '-Name ProxyEnable -Value 0'
        )
        self._run_ps(ps, log)
        log("프록시 설정 초기화 완료", 3)
        return True
