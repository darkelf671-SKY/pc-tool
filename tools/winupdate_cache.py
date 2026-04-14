"""② Windows 업데이트 캐시 삭제"""

import os
import shutil
from tools.base import BaseTool


class WinUpdateCacheTool(BaseTool):
    tool_id = "winupdate_cache"
    name = "Windows 업데이트 캐시 삭제"
    requires_admin = True
    requires_reboot = True

    def get_steps(self):
        return [
            "업데이트 서비스 정지",
            "SoftwareDistribution 삭제",
            "catroot2 삭제",
            "서비스 재시작",
        ]

    def run(self, log):
        services = ["wuauserv", "bits", "cryptsvc"]
        for svc in services:
            self._stop_service(svc, log)
        log("업데이트 관련 서비스 정지 완료", 0)

        sd = r"C:\Windows\SoftwareDistribution"
        if os.path.isdir(sd):
            try:
                shutil.rmtree(sd, ignore_errors=True)
                log("SoftwareDistribution 폴더 삭제 완료", 1)
            except Exception as e:
                log(f"SoftwareDistribution 삭제 오류: {e}", -1)
        else:
            log("SoftwareDistribution 폴더 없음 (skip)", 1)

        cr = r"C:\Windows\System32\catroot2"
        if os.path.isdir(cr):
            try:
                shutil.rmtree(cr, ignore_errors=True)
                log("catroot2 폴더 삭제 완료", 2)
            except Exception as e:
                log(f"catroot2 삭제 오류: {e}", -1)
        else:
            log("catroot2 폴더 없음 (skip)", 2)

        for svc in reversed(services):
            self._start_service(svc, log)
        log("서비스 재시작 완료. 재부팅을 권장합니다.", 3)
        return True
