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
        appdata = os.environ.get("APPDATA", "")
        deleted = 0

        # Classic Teams 메인 데이터 (%APPDATA%)
        classic_roaming = os.path.join(appdata, "Microsoft", "Teams")
        if os.path.isdir(classic_roaming):
            try:
                shutil.rmtree(classic_roaming, ignore_errors=True)
                deleted += 1
                log("  삭제: %APPDATA%\\Microsoft\\Teams (클래식)", -1)
            except Exception:
                pass

        # New Teams UWP 패키지 (%LOCALAPPDATA%)
        new_teams = glob.glob(os.path.join(local, "Packages", "MSTeams_*"))
        for d in new_teams:
            try:
                shutil.rmtree(d, ignore_errors=True)
                deleted += 1
                log(f"  삭제: {os.path.basename(d)}", -1)
            except Exception:
                pass

        # Teams 추가 캐시 + 애드인 (%LOCALAPPDATA%)
        for name in ["Teams", "TeamsMeetingAddin", "TeamsPresenceAddin"]:
            path = os.path.join(local, "Microsoft", name)
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path, ignore_errors=True)
                    deleted += 1
                    log(f"  삭제: %LOCALAPPDATA%\\Microsoft\\{name}", -1)
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

        # Step 3: 재설치 (3단계 폴백)
        installed = False

        # 1차: winget
        log("  [1차] winget 설치 시도...", -1)
        code, output = self._run_cmd(
            "winget install --id Microsoft.Teams --accept-source-agreements --accept-package-agreements",
            log, timeout=120,
        )
        if code == 0:
            installed = True
            log("  → winget 설치 성공", -1)

        # 2차: Windows 프로비저닝 패키지에서 복원
        if not installed:
            log("  [2차] 시스템 프로비저닝 패키지에서 복원 시도...", -1)
            ps_provision = (
                "$pkg = Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | "
                "  Where-Object { $_.DisplayName -like '*MSTeams*' -or $_.DisplayName -like '*MicrosoftTeams*' }; "
                "if ($pkg) { "
                "  foreach ($p in $pkg) { "
                "    Add-AppxPackage -Register $p.InstallLocation -DisableDevelopmentMode "
                "      -ErrorAction SilentlyContinue; "
                "  }; "
                "  Write-Output 'PROVISIONED' "
                "} else { Write-Output 'NOPKG' }"
            )
            code, out = self._run_ps(ps_provision, log, timeout=60)
            if "PROVISIONED" in out:
                installed = True
                log("  → 프로비저닝 패키지 복원 성공", -1)

        # 3차: 다운로드 페이지 열기
        if not installed:
            log("  [3차] 자동 설치 실패 — 다운로드 페이지를 엽니다", -1)
            import webbrowser
            webbrowser.open("https://www.microsoft.com/ko-kr/microsoft-teams/download-app")
            log("  → 브라우저에서 Teams를 다운로드하여 설치하세요", -1)

        if installed:
            log("Teams 재설치 완료", 3)
        else:
            log("Teams 데이터 정리 완료 (수동 설치 필요)", 3)
        return installed
