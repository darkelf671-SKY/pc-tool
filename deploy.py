"""원클릭 배포 — EXE 빌드 + GitHub Release 생성 + 업로드"""
import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

ROOT = Path(__file__).parent
CONFIG_PY = ROOT / "config.py"
DIST_DIR = ROOT / "dist"
EXE_NAME = "PC문제해결도우미.exe"
REPO = "darkelf671-SKY/pc-tool"


# ── 유틸 ──────────────────────────────────────────────────────────

def _get_current_version() -> str:
    """config.py에서 현재 APP_VERSION 읽기"""
    text = CONFIG_PY.read_text(encoding="utf-8")
    m = re.search(r'APP_VERSION\s*=\s*["\'](.+?)["\']', text)
    return m.group(1) if m else "0.0.0"


def _set_version(new_ver: str) -> None:
    """config.py의 APP_VERSION 갱신"""
    text = CONFIG_PY.read_text(encoding="utf-8")
    text = re.sub(
        r'(APP_VERSION\s*=\s*["\'])(.+?)(["\'])',
        rf'\g<1>{new_ver}\g<3>',
        text,
    )
    CONFIG_PY.write_text(text, encoding="utf-8")


def _suggest_next_version(current: str) -> str:
    """1.0.0 → v1.0.1"""
    cleaned = current.strip().lstrip("vV")
    parts = cleaned.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        parts.append("1")
    return "v" + ".".join(parts)


def _check_gh_cli() -> bool:
    """gh CLI 설치 여부 확인"""
    try:
        subprocess.run(["gh", "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_gh_auth() -> bool:
    """gh 인증 상태 확인"""
    try:
        r = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _gh_auth_login() -> bool:
    """gh auth login --web 실행 (브라우저 인증)"""
    try:
        r = subprocess.run(
            ["gh", "auth", "login", "--web", "--git-protocol", "https"],
            timeout=120,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _generate_changelog() -> str:
    """최근 릴리즈 태그 이후 커밋 메시지에서 변경사항 자동 생성"""
    try:
        # 최근 태그 찾기
        tag_result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, timeout=10,
            cwd=str(ROOT),
        )
        if tag_result.returncode == 0:
            last_tag = tag_result.stdout.decode("utf-8", errors="replace").strip()
            log_range = f"{last_tag}..HEAD"
        else:
            log_range = "HEAD~10..HEAD"

        # 커밋 메시지 수집
        log_result = subprocess.run(
            ["git", "log", log_range, "--pretty=format:- %s"],
            capture_output=True, timeout=10,
            cwd=str(ROOT),
        )
        stdout = (log_result.stdout or b"").decode("utf-8", errors="replace").strip()
        if log_result.returncode == 0 and stdout:
            return stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return "- "


def _check_release_exists(tag: str) -> bool:
    """해당 태그의 릴리즈가 이미 존재하는지 확인"""
    try:
        r = subprocess.run(
            ["gh", "release", "view", tag, "--repo", REPO],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ── GUI ───────────────────────────────────────────────────────────

class DeployApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PC 문제해결 도우미 — 원클릭 배포")
        self.resizable(False, False)
        self.configure(bg="#f5f5f5")

        self._current_ver = _get_current_version()
        self._deploying = False

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 4}
        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        # ── 헤더 ──
        ttk.Label(main, text="PC 문제해결 도우미 배포",
                  font=("맑은 고딕", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        # ── 배포 저장소 ──
        ttk.Label(main, text="배포 저장소:").grid(
            row=1, column=0, sticky="w", **pad)
        ttk.Label(main, text=REPO, foreground="#0066cc",
                  font=("Consolas", 10)).grid(
            row=1, column=1, columnspan=2, sticky="w", **pad)

        # ── 현재 버전 ──
        ttk.Label(main, text="현재 버전:").grid(
            row=2, column=0, sticky="w", **pad)
        ttk.Label(main, text=self._current_ver,
                  font=("맑은 고딕", 10, "bold")).grid(
            row=2, column=1, columnspan=2, sticky="w", **pad)

        # ── 배포 버전 ──
        ttk.Label(main, text="배포 버전:").grid(
            row=3, column=0, sticky="w", **pad)
        self._ver_var = tk.StringVar(
            value=_suggest_next_version(self._current_ver))
        ttk.Entry(main, textvariable=self._ver_var, width=20,
                  font=("Consolas", 10)).grid(
            row=3, column=1, sticky="w", **pad)
        ttk.Label(main, text="예: v1.0.1, v1.1.0",
                  foreground="#888").grid(
            row=3, column=2, sticky="w", padx=4)

        # ── 변경사항 ──
        ttk.Label(main, text="변경사항:").grid(
            row=4, column=0, sticky="nw", **pad)
        self._changelog = scrolledtext.ScrolledText(
            main, width=50, height=8,
            font=("맑은 고딕", 9), wrap="word",
            relief="groove", bd=1,
        )
        self._changelog.grid(
            row=4, column=1, columnspan=2, sticky="ew", **pad)
        self._changelog.insert("1.0", _generate_changelog())

        # ── 구분선 ──
        ttk.Separator(main, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=8)

        # ── 상태 ──
        ttk.Label(main, text="상태:").grid(
            row=6, column=0, sticky="w", **pad)
        self._status_var = tk.StringVar(value="준비 완료")
        self._status_label = ttk.Label(
            main, textvariable=self._status_var,
            foreground="#333", font=("맑은 고딕", 9))
        self._status_label.grid(
            row=6, column=1, columnspan=2, sticky="w", **pad)

        # ── 프로그레스 바 ──
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(
            main, variable=self._progress_var,
            maximum=100, length=400)
        self._progress.grid(
            row=7, column=0, columnspan=3, sticky="ew",
            padx=12, pady=(4, 8))

        # ── 로그 ──
        self._log = scrolledtext.ScrolledText(
            main, width=60, height=10,
            font=("Consolas", 8), wrap="word",
            relief="groove", bd=1, state="disabled",
            bg="#1e1e1e", fg="#cccccc",
        )
        self._log.grid(
            row=8, column=0, columnspan=3, sticky="ew",
            padx=12, pady=(0, 8))

        # ── 버튼 ──
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(0, 4))

        self._btn_deploy = ttk.Button(
            btn_frame, text="배포 시작",
            command=self._start_deploy)
        self._btn_deploy.pack(side="left", padx=(12, 8))

        self._btn_cancel = ttk.Button(
            btn_frame, text="닫기",
            command=self._on_close)
        self._btn_cancel.pack(side="right", padx=(8, 12))

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _log_append(self, text: str):
        self._log.config(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.config(state="disabled")
        self.update_idletasks()

    def _set_status(self, text: str, color: str = "#333"):
        self._status_var.set(text)
        self._status_label.config(foreground=color)
        self.update_idletasks()

    def _set_progress(self, value: float):
        self._progress_var.set(value)
        self.update_idletasks()

    def _on_close(self):
        if self._deploying:
            if not messagebox.askyesno("확인", "배포가 진행 중입니다. 닫으시겠습니까?"):
                return
        self.destroy()

    # ── 배포 실행 ──────────────────────────────────────────────

    def _start_deploy(self):
        version = self._ver_var.get().strip()
        changelog = self._changelog.get("1.0", "end").strip()

        if not version:
            messagebox.showwarning("입력 오류", "배포 버전을 입력하세요.")
            return
        if not version.startswith("v"):
            version = "v" + version
            self._ver_var.set(version)
        if not changelog:
            messagebox.showwarning("입력 오류", "변경사항을 입력하세요.")
            return

        self._deploying = True
        self._btn_deploy.config(state="disabled")
        self._ver_var.set(version)

        threading.Thread(
            target=self._deploy_worker,
            args=(version, changelog),
            daemon=True,
        ).start()

    def _deploy_worker(self, version: str, changelog: str):
        try:
            self._do_deploy(version, changelog)
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _do_deploy(self, version: str, changelog: str):
        # ── Step 1: gh CLI 확인 ──
        self.after(0, lambda: self._set_status("[1/8] gh CLI 확인 중..."))
        self.after(0, lambda: self._set_progress(5))
        self.after(0, lambda: self._log_append("[1/8] gh CLI 설치 확인..."))

        if not _check_gh_cli():
            self.after(0, lambda: self._on_error(
                "gh CLI가 설치되어 있지 않습니다.\n\n"
                "설치 방법:\n"
                "  winget install GitHub.cli\n"
                "  또는 https://cli.github.com 에서 다운로드"))
            return

        self.after(0, lambda: self._log_append("  → gh CLI 확인 완료"))

        # ── Step 2: GitHub 인증 ──
        self.after(0, lambda: self._set_status("[2/8] GitHub 인증 확인 중..."))
        self.after(0, lambda: self._set_progress(15))
        self.after(0, lambda: self._log_append("[2/8] GitHub 인증 상태 확인..."))

        if not _check_gh_auth():
            self.after(0, lambda: self._log_append(
                "  → 미인증 상태. 브라우저 인증을 시작합니다..."))
            self.after(0, lambda: self._set_status(
                "[2/8] 브라우저에서 GitHub 로그인 중...", "#cc6600"))

            if not _gh_auth_login():
                self.after(0, lambda: self._on_error(
                    "GitHub 인증에 실패했습니다.\n"
                    "터미널에서 'gh auth login' 을 직접 실행해 보세요."))
                return

        self.after(0, lambda: self._log_append("  → GitHub 인증 완료"))

        # ── Step 2.5: 릴리즈 중복 확인 ──
        self.after(0, lambda: self._log_append(
            f"  → 릴리즈 태그 '{version}' 중복 확인..."))
        if _check_release_exists(version):
            self.after(0, lambda: self._on_error(
                f"'{version}' 릴리즈가 이미 존재합니다.\n"
                f"다른 버전 번호를 사용하세요."))
            return
        self.after(0, lambda: self._log_append("  → 중복 없음"))

        # ── Step 3: 도구 자동 검증 ──
        self.after(0, lambda: self._set_status("[3/8] 도구 자동 검증 중..."))
        self.after(0, lambda: self._set_progress(20))
        self.after(0, lambda: self._log_append(
            "[3/8] verify_tools.py 실행 (16개 도구 계약 검증)..."))

        verify_result = subprocess.run(
            [sys.executable, str(ROOT / "verify_tools.py")],
            capture_output=True, text=True,
            cwd=str(ROOT), timeout=60,
        )

        if verify_result.returncode != 0:
            output = verify_result.stdout or verify_result.stderr or ""
            # FAIL 줄만 추출
            fail_lines = [l for l in output.splitlines() if "[FAIL]" in l]
            for line in fail_lines:
                self.after(0, lambda l=line: self._log_append(f"  {l.strip()}"))
            self.after(0, lambda: self._on_error(
                "도구 검증 실패 - 배포가 차단됩니다.\n\n"
                + "\n".join(fail_lines[:5])))
            return

        self.after(0, lambda: self._log_append("  -> 16개 도구 검증 통과"))

        # ── Step 4: APP_VERSION 갱신 ──
        self.after(0, lambda: self._set_status("[4/8] 버전 갱신 중..."))
        self.after(0, lambda: self._set_progress(30))
        self.after(0, lambda: self._log_append(
            f"[4/8] config.py APP_VERSION: {self._current_ver} → {version}"))

        _set_version(version.lstrip("v"))
        self.after(0, lambda: self._log_append("  → 버전 갱신 완료"))

        # ── Step 5: git commit + push ──
        self.after(0, lambda: self._set_status("[5/8] git 커밋 + 푸시 중..."))
        self.after(0, lambda: self._set_progress(35))
        self.after(0, lambda: self._log_append(
            f"[5/8] 변경사항 git 커밋 + 푸시..."))

        # 모든 변경 파일 스테이징 + 커밋
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(ROOT), capture_output=True, timeout=30,
        )
        commit_result = subprocess.run(
            ["git", "commit", "-m", f"release: {version}"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=30,
        )
        if commit_result.returncode == 0:
            self.after(0, lambda: self._log_append("  → 커밋 완료"))
        else:
            self.after(0, lambda: self._log_append(
                "  → 커밋 스킵 (변경사항 없음 또는 이미 커밋됨)"))

        push_result = subprocess.run(
            ["git", "push"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60,
        )
        if push_result.returncode == 0:
            self.after(0, lambda: self._log_append("  → 푸시 완료"))
        else:
            err = push_result.stderr or push_result.stdout or ""
            self.after(0, lambda: self._log_append(f"  → 푸시 실패: {err[:200]}"))
            self.after(0, lambda: self._on_error(
                f"git push에 실패했습니다.\n{err[:300]}"))
            return

        # ── Step 6: EXE 빌드 ──
        self.after(0, lambda: self._set_status("[6/8] EXE 빌드 중... (1~2분 소요)"))
        self.after(0, lambda: self._set_progress(45))
        self.after(0, lambda: self._log_append(
            "[6/8] EXE 빌드 시작 (PyInstaller)..."))

        build_result = subprocess.run(
            [sys.executable, str(ROOT / "build_exe.py")],
            capture_output=True, text=True,
            cwd=str(ROOT), timeout=600,
        )

        if build_result.returncode != 0:
            # 빌드 실패 시 버전 롤백
            _set_version(self._current_ver)
            err_msg = build_result.stderr or build_result.stdout or "알 수 없는 오류"
            self.after(0, lambda: self._log_append(f"  [ERROR] {err_msg[-500:]}"))
            self.after(0, lambda: self._on_error(
                f"EXE 빌드에 실패했습니다.\n버전이 {self._current_ver}로 복원되었습니다."))
            return

        exe_path = DIST_DIR / EXE_NAME
        if not exe_path.exists():
            _set_version(self._current_ver)
            self.after(0, lambda: self._on_error("빌드 완료되었지만 EXE 파일을 찾을 수 없습니다."))
            return

        size_mb = exe_path.stat().st_size / (1024 * 1024)
        self.after(0, lambda: self._log_append(
            f"  → 빌드 완료: {EXE_NAME} ({size_mb:.1f} MB)"))
        self.after(0, lambda: self._set_progress(75))

        # ── Step 6: GitHub Release 생성 + 업로드 ──
        self.after(0, lambda: self._set_status("[7/8] GitHub Release 업로드 중..."))
        self.after(0, lambda: self._log_append(
            f"[7/8] GitHub Release 생성: {version}"))
        self.after(0, lambda: self._log_append(
            f"  → 저장소: {REPO}"))
        self.after(0, lambda: self._log_append(
            f"  → 파일: {exe_path}"))

        release_result = subprocess.run(
            [
                "gh", "release", "create", version,
                str(exe_path),
                "--repo", REPO,
                "--title", version,
                "--notes", changelog,
            ],
            capture_output=True, text=True,
            timeout=300,
        )

        if release_result.returncode != 0:
            err = release_result.stderr or release_result.stdout or "알 수 없는 오류"
            self.after(0, lambda: self._log_append(f"  [ERROR] {err}"))
            self.after(0, lambda: self._on_error(
                f"GitHub Release 생성에 실패했습니다.\n\n{err}"))
            return

        release_url = release_result.stdout.strip()
        self.after(0, lambda: self._log_append(
            f"  → 업로드 완료!"))
        self.after(0, lambda: self._log_append(
            f"  → {release_url}"))
        self.after(0, lambda: self._set_progress(95))

        # ── Step 7: 완료 ──
        self.after(0, lambda: self._set_status("[8/8] 배포 완료!"))
        self.after(0, lambda: self._log_append(
            f"[8/8] 배포 완료: {version}"))
        self.after(0, lambda: self._set_progress(100))
        self.after(0, lambda: self._on_success(version, release_url))

    def _on_success(self, version: str, url: str):
        self._deploying = False
        self._set_status(f"배포 완료! ({version})", "#008800")
        self._btn_deploy.config(state="normal")
        messagebox.showinfo(
            "배포 완료",
            f"배포가 성공적으로 완료되었습니다!\n\n"
            f"버전: {version}\n"
            f"Release: {url}")

    def _on_error(self, msg: str):
        self._deploying = False
        self._set_status("오류 발생", "#cc0000")
        self._btn_deploy.config(state="normal")
        messagebox.showerror("배포 오류", msg)


if __name__ == "__main__":
    app = DeployApp()
    app.mainloop()
