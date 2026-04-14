"""③ 브라우저 초기화 (SSL + 프록시 포함)"""

import os
import shutil
from tools.base import BaseTool


class BrowserResetTool(BaseTool):
    tool_id = "browser_reset"
    name = "브라우저 초기화"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return [
            "브라우저 프로세스 종료",
            "Edge/Chrome 캐시 삭제",
            "SSL 인증서 캐시 초기화",
            "프록시 설정 초기화",
        ]

    def run(self, log):
        # Step 0: 브라우저 종료
        for proc in ["msedge.exe", "chrome.exe"]:
            self._run_cmd(f"taskkill /F /IM {proc}", log)
        log("브라우저 프로세스 종료", 0)

        # Step 1: 캐시 삭제
        local = os.environ.get("LOCALAPPDATA", "")
        cache_dirs = [
            os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache"),
            os.path.join(local, r"Microsoft\Edge\User Data\Default\Code Cache"),
            os.path.join(local, r"Google\Chrome\User Data\Default\Cache"),
            os.path.join(local, r"Google\Chrome\User Data\Default\Code Cache"),
        ]
        deleted = 0
        for d in cache_dirs:
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
                deleted += 1
        log(f"브라우저 캐시 {deleted}개 폴더 삭제", 1)

        # Step 2: SSL 인증서 캐시
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
        log("프록시 설정 초기화 완료. 브라우저를 다시 열어주세요.", 3)
        return True
