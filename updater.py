"""GitHub Release 자동 업데이트 — 사용자 확인 없이 자동 실행"""

import json
import os
import sys
import subprocess
import tempfile
import time


class Updater:
    def __init__(self, current_version: str, repo: str):
        self._current = current_version
        self._api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        self._cache_file = self._get_cache_path()

    def _get_cache_path(self) -> str:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "data", ".update_cache.json")

    def _load_cache(self) -> dict:
        try:
            with open(self._cache_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cache(self, data: dict):
        try:
            os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def check_and_update(self) -> bool:
        """
        새 버전 있으면 자동 다운로드 → EXE 교체 → 재시작.
        Returns: True=업데이트 진행(앱 종료 필요), False=최신 버전
        """
        # GitHub 접속 불가 캐시: 마지막 실패 후 1시간 동안 재시도 안 함
        cache = self._load_cache()
        last_fail = cache.get("last_fail", 0)
        if time.time() - last_fail < 3600:
            return False

        try:
            import requests
            resp = requests.get(self._api_url, timeout=3)
            if resp.status_code != 200:
                self._save_cache({"last_fail": time.time()})
                return False

            release = resp.json()
            latest = release.get("tag_name", "").lstrip("v")

            if not self._is_newer(latest, self._current):
                # 최신 버전 — 실패 캐시 초기화
                self._save_cache({})
                return False

            asset = self._find_exe_asset(release.get("assets", []))
            if not asset:
                return False

            new_exe = self._download(asset["browser_download_url"])
            self._replace_and_restart(new_exe)
            return True

        except Exception:
            self._save_cache({"last_fail": time.time()})
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
