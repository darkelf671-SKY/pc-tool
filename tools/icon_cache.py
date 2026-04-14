"""⑨ 아이콘 캐시 초기화"""

import os
import time
from tools.base import BaseTool


class IconCacheTool(BaseTool):
    tool_id = "icon_cache"
    name = "아이콘 캐시 초기화"
    requires_admin = False
    requires_reboot = False

    def get_steps(self):
        return ["탐색기 종료", "아이콘 캐시 삭제", "탐색기 재시작"]

    def run(self, log):
        # Step 0: 탐색기 종료
        self._run_cmd("taskkill /F /IM explorer.exe", log)
        log("탐색기 종료", 0)
        time.sleep(1)

        # Step 1: 아이콘 캐시 삭제
        local = os.environ.get("LOCALAPPDATA", "")
        deleted = 0

        icon_db = os.path.join(local, "IconCache.db")
        if os.path.isfile(icon_db):
            try:
                os.remove(icon_db)
                deleted += 1
            except Exception:
                pass

        explorer_cache = os.path.join(
            local, "Microsoft", "Windows", "Explorer"
        )
        if os.path.isdir(explorer_cache):
            deleted += self._delete_files(explorer_cache, log, "iconcache_*")
            deleted += self._delete_files(explorer_cache, log, "thumbcache_*")

        log(f"캐시 파일 {deleted}개 삭제", 1)

        # Step 2: 탐색기 재시작
        self._run_cmd("start explorer.exe", log)
        log("탐색기 재시작 완료", 2)
        return True
