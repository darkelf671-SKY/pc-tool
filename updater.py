"""GitHub Release 자동 업데이트 — 사용자 확인 없이 자동 실행"""

import os
import sys
import subprocess
import tempfile


class Updater:
    def __init__(self, current_version: str, repo: str):
        self._current = current_version
        self._api_url = f"https://api.github.com/repos/{repo}/releases/latest"

    def check_and_update(self) -> bool:
        """
        새 버전 있으면 자동 다운로드 → EXE 교체 → 재시작.
        Returns: True=업데이트 진행(앱 종료 필요), False=최신 버전
        """
        try:
            import requests
            resp = requests.get(self._api_url, timeout=5)
            if resp.status_code != 200:
                return False

            release = resp.json()
            latest = release.get("tag_name", "").lstrip("v")

            if not self._is_newer(latest, self._current):
                return False

            asset = self._find_exe_asset(release.get("assets", []))
            if not asset:
                return False

            new_exe = self._download(asset["browser_download_url"])
            self._replace_and_restart(new_exe)
            return True

        except Exception:
            return False

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
        """BAT 스크립트로 EXE 교체 후 재시작 (파일 잠금 우회)"""
        current_exe = sys.executable
        bat_script = f"""@echo off
timeout /t 2 /nobreak >nul
copy /y "{new_exe}" "{current_exe}"
del "{new_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        bat_path = new_exe + ".bat"
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_script)
        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        sys.exit(0)
