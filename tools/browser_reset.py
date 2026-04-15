"""③ 브라우저 초기화 (전체 인터넷 사용 기록 삭제)"""

import os
import shutil
import time
from tools.base import BaseTool


# 삭제 대상 (로그인 정보·북마크·확장 프로그램은 보존)
# 실제 Edge/Chrome 프로필 폴더 구조 기준 (Chromium 96+)
_BROWSER_TARGETS = [
    # ── 캐시 (이미지, JS, CSS 등) ──
    "Cache",
    "Code Cache",
    "GPUCache",
    "DawnGraphiteCache",
    "DawnWebGPUCache",
    "image_cache",
    "Storage",
    "blob_storage",
    "shared_proto_db",
    # ── 쿠키 (Chromium 96+: Network 하위로 이동됨) ──
    "Network",
    # ── 사이트 데이터 ──
    "Local Storage",
    "Session Storage",
    "IndexedDB",
    "Service Worker",
    "File System",
    "databases",
    "SharedStorage",
    "SharedStorage-wal",
    "Shared Dictionary",
    # ── 검색 기록 ──
    "History",
    "History-journal",
    "Visited Links",
    "Top Sites",
    "Top Sites-journal",
    "BrowsingTopicsSiteData",
    "BrowsingTopicsSiteData-journal",
    "BrowsingTopicsState",
    # ── 기타 웹 데이터 ──
    "Web Data",
    "Web Data-journal",
    "Shortcuts",
    "Shortcuts-journal",
    "DIPS",
    "DIPS-wal",
    "InterestGroups",
    "InterestGroups-wal",
    "PrivateAggregation",
    "PrivateAggregation-journal",
    "Platform Notifications",
    "Feature Engagement Tracker",
    # ── 구버전 호환 (Chromium 96 이전 쿠키 위치) ──
    "Cookies",
    "Cookies-journal",
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
        ]

    def run(self, log):
        # Step 0: 브라우저 종료
        for proc in ["msedge.exe", "chrome.exe"]:
            self._run_cmd(f"taskkill /F /IM {proc}", log)
        time.sleep(1)  # 파일 핸들 해제 대기
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

        log("브라우저를 다시 열어주세요.", -1)
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
