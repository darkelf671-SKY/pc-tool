"""GitHub Release 자동 업데이트 — 진행 상태 UI + 안정적 EXE 교체"""

import os
import sys
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import ttk


class Updater:
    def __init__(self, current_version: str, repo: str):
        self._current = current_version
        self._api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        self._root: tk.Tk | None = None
        self._status_var: tk.StringVar | None = None
        self._progress: ttk.Progressbar | None = None

    def check_and_update(self) -> str:
        """
        새 버전 있으면 자동 다운로드 → EXE 교체 → 재시작.
        Returns:
            "updated" — 업데이트 진행 중 (앱 종료됨)
            "latest"  — 이미 최신 버전
            "failed"  — 업데이트 확인/다운로드 실패
        """
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

            # 업데이트 발견 → 진행 UI 표시 + 다운로드
            size = asset.get("size", 0)
            new_exe = self._download_with_ui(
                asset["browser_download_url"], latest, size,
            )
            if not new_exe:
                return "failed"

            self._replace_and_restart(new_exe)
            return "updated"

        except Exception:
            return "failed"

    # ── 버전 비교 ──

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

    # ── 진행 UI + 다운로드 ──

    def _download_with_ui(self, url: str, version: str, total_size: int) -> str | None:
        """tkinter 진행 창 + 백그라운드 다운로드"""
        self._root = tk.Tk()
        self._root.title("업데이트")
        self._root.resizable(False, False)
        self._root.configure(bg="#f5f5f5")
        self._root.overrideredirect(False)
        self._root.attributes("-topmost", True)

        frame = ttk.Frame(self._root, padding=24)
        frame.pack()

        ttk.Label(
            frame, text=f"v{version} 업데이트 다운로드 중",
            font=("맑은 고딕", 12, "bold"),
        ).pack(pady=(0, 8))

        self._status_var = tk.StringVar(value="다운로드 준비 중...")
        ttk.Label(
            frame, textvariable=self._status_var,
            font=("맑은 고딕", 9),
        ).pack(pady=(0, 12))

        self._progress = ttk.Progressbar(frame, length=320, mode="determinate")
        self._progress.pack(pady=(0, 8))

        # 창 중앙 배치
        self._root.update_idletasks()
        w, h = self._root.winfo_width(), self._root.winfo_height()
        x = (self._root.winfo_screenwidth() - w) // 2
        y = (self._root.winfo_screenheight() - h) // 2
        self._root.geometry(f"+{x}+{y}")

        result = {"path": None}

        def _worker():
            try:
                import requests
                resp = requests.get(url, stream=True, timeout=120)
                content_length = int(resp.headers.get("content-length", total_size))
                if content_length == 0:
                    content_length = total_size

                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".exe")
                downloaded = 0

                for chunk in resp.iter_content(8192):
                    tmp.write(chunk)
                    downloaded += len(chunk)
                    if content_length > 0:
                        pct = min(downloaded / content_length * 100, 100)
                        mb_done = downloaded / 1024 / 1024
                        mb_total = content_length / 1024 / 1024
                        self._root.after(0, lambda p=pct, d=mb_done, t=mb_total: (
                            self._progress.configure(value=p),
                            self._status_var.set(f"{d:.1f} / {t:.1f} MB ({p:.0f}%)"),
                        ))

                tmp.close()
                result["path"] = tmp.name
                self._root.after(0, lambda: (
                    self._status_var.set("다운로드 완료! 업데이트 적용 중..."),
                    self._root.after(800, self._root.destroy),
                ))
            except Exception:
                self._root.after(0, self._root.destroy)

        threading.Thread(target=_worker, daemon=True).start()
        self._root.mainloop()
        return result["path"]

    # ── EXE 교체 + 재시작 ──

    def _replace_and_restart(self, new_exe: str):
        """PowerShell 스크립트로 EXE 교체 후 재시작"""
        current_exe = sys.executable
        mei_dir = getattr(sys, "_MEIPASS", "")
        # 1) 프로세스 종료 대기  2) _MEI 임시폴더 정리  3) EXE 복사  4) 재시작
        ps_script = (
            "$maxWait = 15; $waited = 0; "
            f"while ((Get-Process | Where-Object {{ $_.Path -eq '{current_exe}' }}) -and ($waited -lt $maxWait)) {{ "
            "  Start-Sleep -Milliseconds 500; $waited++; "
            "}; "
            "Start-Sleep -Seconds 2; "
            # _MEI 임시폴더 잔존 시 삭제 (python311.dll 충돌 방지)
            f"if (Test-Path -LiteralPath '{mei_dir}') {{ "
            f"  Remove-Item -LiteralPath '{mei_dir}' -Recurse -Force -ErrorAction SilentlyContinue; "
            "}; "
            f"Copy-Item -LiteralPath '{new_exe}' -Destination '{current_exe}' -Force; "
            f"if (Test-Path -LiteralPath '{current_exe}') {{ "
            f"  Remove-Item -LiteralPath '{new_exe}' -Force; "
            f"  Start-Process -FilePath '{current_exe}' -Verb RunAs; "
            "} "
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        sys.exit(0)
