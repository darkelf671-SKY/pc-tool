"""⑥ 임시파일 정리"""

import os
import shutil
from tools.base import BaseTool


class TempCleanupTool(BaseTool):
    tool_id = "temp_cleanup"
    name = "임시파일 정리"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return ["사용자 Temp 정리", "Windows Temp 정리",
                "Prefetch 정리", "휴지통 비우기"]

    def run(self, log):
        total = 0

        # Step 0: 사용자 Temp
        user_temp = os.environ.get("TEMP", "")
        if user_temp and os.path.isdir(user_temp):
            cnt = self._delete_files(user_temp, log)
            total += cnt
            log(f"사용자 Temp: {cnt}개 파일 삭제", 0)
        else:
            log("사용자 Temp 폴더 없음", 0)

        # Step 1: Windows Temp
        win_temp = r"C:\Windows\Temp"
        if os.path.isdir(win_temp):
            cnt = self._delete_files(win_temp, log)
            total += cnt
            log(f"Windows Temp: {cnt}개 파일 삭제", 1)
        else:
            log("Windows Temp 폴더 없음", 1)

        # Step 2: Prefetch
        prefetch = r"C:\Windows\Prefetch"
        if os.path.isdir(prefetch):
            cnt = self._delete_files(prefetch, log)
            total += cnt
            log(f"Prefetch: {cnt}개 파일 삭제", 2)
        else:
            log("Prefetch 폴더 없음", 2)

        # Step 3: 휴지통
        self._run_ps(
            "Clear-RecycleBin -Force -ErrorAction SilentlyContinue", log
        )
        log(f"휴지통 비우기 완료. 총 {total}개 파일 정리.", 3)
        return True
