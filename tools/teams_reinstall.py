"""⑮ Teams 클린삭제 + 재설치"""

import os
import shutil
import glob
from tools.base import BaseTool


class TeamsReinstallTool(BaseTool):
    tool_id = "teams_reinstall"
    name = "Teams 클린 재설치"
    requires_admin = True
    requires_reboot = False

    def get_steps(self):
        return [
            "Teams 프로세스 종료",
            "Teams 데이터 삭제",
            "Teams 패키지 제거",
            "Teams 재설치",
        ]

    def run(self, log):
        # Step 0: Teams 프로세스 종료
        self._run_cmd("taskkill /F /IM ms-teams.exe", log, timeout=10)
        self._run_cmd("taskkill /F /IM Teams.exe", log, timeout=10)
        log("Teams 프로세스 종료 완료", 0)

        # Step 1: Teams 데이터 삭제
        local = os.environ.get("LOCALAPPDATA", "")
        deleted = 0

        # New Teams data
        new_teams = glob.glob(os.path.join(local, "Packages", "MSTeams_*"))
        for d in new_teams:
            try:
                shutil.rmtree(d, ignore_errors=True)
                deleted += 1
                log(f"  삭제: {os.path.basename(d)}", -1)
            except Exception:
                pass

        # Classic Teams remnants
        classic_path = os.path.join(local, "Microsoft", "Teams")
        if os.path.isdir(classic_path):
            try:
                shutil.rmtree(classic_path, ignore_errors=True)
                deleted += 1
                log("  삭제: Microsoft\\Teams (클래식)", -1)
            except Exception:
                pass

        log(f"Teams 데이터 {deleted}개 폴더 삭제 완료", 1)

        # Step 2: 패키지 완전 제거
        ps_remove = (
            "Get-AppxPackage *MSTeams* | Remove-AppxPackage -ErrorAction SilentlyContinue; "
            "Get-AppxPackage *MicrosoftTeams* | Remove-AppxPackage -ErrorAction SilentlyContinue; "
            "Write-Output 'DONE'"
        )
        code, output = self._run_ps(ps_remove, log, timeout=30)
        log("Teams 패키지 제거 완료", 2)

        # Step 3: 재설치 (winget)
        code, output = self._run_cmd(
            "winget install --id Microsoft.Teams --accept-source-agreements --accept-package-agreements",
            log, timeout=120,
        )
        if code == 0:
            log("Teams 재설치 완료", 3)
            return True
        else:
            # winget 실패 시 안내
            log("winget 설치 실패 — 수동 설치가 필요할 수 있습니다", -1)
            log("Microsoft Teams 다운로드: https://www.microsoft.com/ko-kr/microsoft-teams/download-app", -1)
            log("Teams 데이터는 정리 완료되었습니다", 3)
            return False
