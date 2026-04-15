"""③ 브라우저 초기화 (전체 인터넷 사용 기록 삭제 + SSL + 프록시)"""

import os
import shutil
from tools.base import BaseTool


# 삭제 대상 (로그인 정보·북마크·확장 프로그램은 보존)
_BROWSER_TARGETS = [
    # 캐시된 이미지 및 파일
    "Cache",
    "Code Cache",
    "GPUCache",
    "ShaderCache",
    "Storage\\ext",
    # 쿠키 및 사이트 데이터
    "Cookies",
    "Cookies-journal",
    "Local Storage",
    "Session Storage",
    "IndexedDB",
    "Service Worker",
    "File System",
    "databases",
    # 검색 기록
    "History",
    "History-journal",
    "Visited Links",
    "Top Sites",
    "Top Sites-journal",
    # 기타 웹 데이터
    "Web Data",
    "Web Data-journal",
]


class BrowserResetTool(BaseTool):
    tool_id = "browser_reset"
    name = "브라우저 초기화"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return [
            "브라우저 프로세스 종료",
            "Edge 인터넷 사용 기록 삭제",
            "Chrome 인터넷 사용 기록 삭제",
            "SSL 인증서 캐시 초기화",
            "프록시 설정 초기화",
        ]

    def run(self, log):
        # Step 0: 브라우저 종료
        for proc in ["msedge.exe", "chrome.exe"]:
            self._run_cmd(f"taskkill /F /IM {proc}", log)
        log("브라우저 프로세스 종료", 0)

        local = os.environ.get("LOCALAPPDATA", "")

        # Step 1: Edge 사용 기록 삭제
        edge_profile = os.path.join(local, r"Microsoft\Edge\User Data\Default")
        cnt = self._clear_browser_data(edge_profile)
        log(f"Edge: {cnt}개 항목 삭제 (캐시/쿠키/기록/사이트 데이터)", 1)

        # Step 2: Chrome 사용 기록 삭제
        chrome_profile = os.path.join(local, r"Google\Chrome\User Data\Default")
        cnt = self._clear_browser_data(chrome_profile)
        log(f"Chrome: {cnt}개 항목 삭제 (캐시/쿠키/기록/사이트 데이터)", 2)

        # Step 3: SSL 인증서 캐시
        self._run_cmd("certutil -urlcache * delete", log)
        log("SSL 인증서 캐시 초기화 완료", 3)

        # Step 4: 프록시 설정 초기화
        ps = (
            'Set-ItemProperty '
            '-Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion'
            '\\Internet Settings" '
            '-Name ProxyEnable -Value 0'
        )
        self._run_ps(ps, log)
        log("프록시 설정 초기화 완료. 브라우저를 다시 열어주세요.", 4)
        return True

    def _clear_browser_data(self, profile_dir: str) -> int:
        """프로필 폴더에서 인터넷 사용 기록 삭제 (로그인·북마크 보존)"""
        if not os.path.isdir(profile_dir):
            return 0

        deleted = 0
        for target in _BROWSER_TARGETS:
            path = os.path.join(profile_dir, target)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
                deleted += 1
            elif os.path.isfile(path):
                try:
                    os.remove(path)
                    deleted += 1
                except OSError:
                    pass
        return deleted
