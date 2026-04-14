"""GitHub Release 자동 업데이트 — 실패 시 사용자 알림"""

import os
import sys
import subprocess
import tempfile


class Updater:
    def __init__(self, current_version: str, repo: str):
        self._current = current_version
        self._api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    def check_and_update(self) -> str:
        """
        새 버전 있으면 자동 다운로드 → EXE 교체 → 재시작.
        Returns:
            "updated" — 업데이트 진행 중 (앱 종료됨)
            "latest"  — 이미 최신 버전
            "failed"  — 업데이트 확인/다운로드 실패
        """
        # 개발 환경(python main.py)에서는 업데이트 안 함
        if not getattr(sys, "frozen", False):
            return "latest"

        try:
            import requests
            resp = requests.get(self._api_url, timeout=3)
            if resp.status_code != 200:
                return "failed"

            release = resp.json()
            latest = release.get("tag_name", "").lstrip("v")

            if not self._is_newer(latest, self._current):
                return "latest"

            asset = self._find_exe_asset(release.get("assets", []))
            if not asset:
                return "failed"

            new_exe = self._download(asset["browser_download_url"])
            self._replace_and_restart(new_exe)
            return "updated"

        except Exception:
            return "failed"

    def _is_newer(self, latest: str, current: str) -> bool:
        try:
            lparts = [int(x) for x in latest.split(".")]
            cparts = [int(x) for x in current.split(".")]
            return lparts > cparts
        except Exception:
            return latest != current

    def _find_exe_asset(self, assets: list[dict]) -> dict | None:
        for a in assets:
            if a.get("name", "").endswith(".exe"):
                return a
        return None

    def _download(self, url: str) -> str:
        import requests
        resp = requests.get(url, stream=True, timeout=120)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".exe")
        for chunk in resp.iter_content(8192):
            tmp.write(chunk)
        tmp.close()
        return tmp.name

    def _replace_and_restart(self, new_exe: str):
        """PowerShell 스크립트로 EXE 교체 후 재시작 (파일 잠금 + 한글 경로 대응)"""
        current_exe = sys.executable
        ps_script = (
            f"Start-Sleep -Seconds 3; "
            f"Copy-Item -LiteralPath '{new_exe}' -Destination '{current_exe}' -Force; "
            f"Remove-Item -LiteralPath '{new_exe}' -Force; "
            f"Start-Process -FilePath '{current_exe}'; "
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        sys.exit(0)
