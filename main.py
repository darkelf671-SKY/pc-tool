"""PC 문제해결 도우미 — 진입점 (pywebview)"""

import ctypes
import subprocess
import sys
import os
import winreg


def _fix_tcl_path():
    """PyInstaller frozen 환경에서 Tcl/Tk 경로 설정"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        tcl = os.path.join(base, "tcl8.6")
        tk = os.path.join(base, "tk8.6")
        if os.path.isdir(tcl):
            os.environ["TCL_LIBRARY"] = tcl
        if os.path.isdir(tk):
            os.environ["TK_LIBRARY"] = tk


def set_dpi_awareness():
    """DPI 인식 설정"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def ensure_admin():
    """관리자 권한 없으면 UAC 승격 재실행"""
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            script = os.path.abspath(sys.argv[0])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}"', None, 1,
            )
            sys.exit(0)
    except Exception:
        pass


def _check_webview2() -> bool:
    """WebView2 Runtime 설치 여부 확인 (API 호출 → 레지스트리 → 폴더 순)"""
    # 1순위: 레지스트리 확인
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients"
         r"\{F3017226-FE2A-4295-8BEE-13A6279FE7F8}"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\EdgeUpdate\Clients"
         r"\{F3017226-FE2A-4295-8BEE-13A6279FE7F8}"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\EdgeUpdate\Clients"
         r"\{F3017226-FE2A-4295-8BEE-13A6279FE7F8}"),
    ]
    for hive, path in reg_paths:
        try:
            with winreg.OpenKey(hive, path) as key:
                val, _ = winreg.QueryValueEx(key, "pv")
                if val and val != "0.0.0.0":
                    return True
        except OSError:
            continue

    # 3순위: 설치 폴더 존재 확인
    webview_dirs = [
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "EdgeWebView"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "EdgeWebView"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "EdgeWebView"),
    ]
    for d in webview_dirs:
        if d and os.path.isdir(d):
            return True

    return False


def _install_webview2():
    """WebView2 Runtime 자동 설치 (진행 상태 표시)"""
    import threading
    import tkinter as tk
    from tkinter import ttk, messagebox

    # 진행 상태 창
    root = tk.Tk()
    root.title("WebView2 설치")
    root.resizable(False, False)
    root.configure(bg="#f5f5f5")

    frame = ttk.Frame(root, padding=24)
    frame.pack()

    ttk.Label(frame, text="WebView2 Runtime 설치 중",
              font=("맑은 고딕", 12, "bold")).pack(pady=(0, 8))

    status_var = tk.StringVar(value="설치 준비 중...")
    ttk.Label(frame, textvariable=status_var,
              font=("맑은 고딕", 9)).pack(pady=(0, 12))

    progress = ttk.Progressbar(frame, mode="indeterminate", length=300)
    progress.pack(pady=(0, 8))
    progress.start(15)

    # 창 중앙 배치
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"+{x}+{y}")

    result = {"success": False}
    NO_WINDOW = subprocess.CREATE_NO_WINDOW

    def _worker():
        # winget 시도
        root.after(0, lambda: status_var.set("winget으로 설치 시도 중..."))
        try:
            r = subprocess.run(
                ["winget", "install", "--id",
                 "Microsoft.EdgeWebView2Runtime",
                 "--accept-source-agreements",
                 "--accept-package-agreements", "--silent"],
                capture_output=True, timeout=120,
                creationflags=NO_WINDOW,
            )
            if r.returncode == 0 and _check_webview2():
                result["success"] = True
                root.after(0, _on_done)
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 직접 다운로드
        root.after(0, lambda: status_var.set("다운로드 중... (잠시만 기다려주세요)"))
        try:
            import tempfile
            import requests
            url = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
            tmp = os.path.join(tempfile.gettempdir(), "MicrosoftEdgeWebview2Setup.exe")
            resp = requests.get(url, stream=True, timeout=60)
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)

            root.after(0, lambda: status_var.set("설치 진행 중..."))
            subprocess.run(
                [tmp, "/silent", "/install"],
                timeout=120, creationflags=NO_WINDOW,
            )
            if _check_webview2():
                result["success"] = True
                root.after(0, _on_done)
                return
        except Exception:
            pass

        root.after(0, _on_done)

    def _on_done():
        progress.stop()
        root.destroy()

    threading.Thread(target=_worker, daemon=True).start()
    root.mainloop()

    if result["success"]:
        return True

    # 실패 시 브라우저로 수동 설치 안내
    import webbrowser
    r2 = tk.Tk()
    r2.withdraw()
    messagebox.showinfo(
        "수동 설치 필요",
        "WebView2 자동 설치에 실패했습니다.\n\n"
        "확인을 누르면 다운로드 페이지가 열립니다.\n"
        "설치 완료 후 프로그램을 다시 실행해주세요.",
    )
    webbrowser.open("https://developer.microsoft.com/microsoft-edge/webview2")
    r2.destroy()
    return False


def _html_path() -> str:
    """index.html 경로 (EXE/개발 환경 대응)"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "ui", "index.html")


def _apply_pending_update():
    """이전 업데이트에서 남은 pending EXE 적용 + .old 정리"""
    if not getattr(sys, "frozen", False):
        return

    import shutil
    current_exe = sys.executable
    app_dir = os.path.dirname(current_exe)
    pending = os.path.join(app_dir, "update_pending.exe")
    bak = current_exe + ".old"

    # .old 정리 (이전 업데이트 잔여)
    if os.path.exists(bak):
        try:
            os.remove(bak)
        except OSError:
            pass

    if not os.path.exists(pending):
        return

    # pending EXE → 현재 위치에 적용
    try:
        os.rename(current_exe, bak)
        shutil.copy2(pending, current_exe)
        if os.path.getsize(current_exe) == os.path.getsize(pending):
            # 성공: 정리 + 새 EXE로 재시작
            for f in (bak, pending):
                try:
                    os.remove(f)
                except OSError:
                    pass
            subprocess.Popen([current_exe])
            sys.exit(0)
        else:
            # 크기 불일치: 롤백
            os.remove(current_exe)
            os.rename(bak, current_exe)
    except OSError:
        pass

    # 실패 시 pending 삭제 (무한 재시도 방지)
    try:
        os.remove(pending)
    except OSError:
        pass


def main():
    _fix_tcl_path()
    set_dpi_awareness()
    ensure_admin()
    _apply_pending_update()

    # WebView2 Runtime 확인 + 자동 설치
    if not _check_webview2():
        if not _install_webview2():
            sys.exit(1)
        # 설치 후 자기 자신 재시작
        script = os.path.abspath(sys.argv[0])
        os.execv(sys.executable, [sys.executable, script])

    # 자동 업데이트 (UI 표시 전)
    from updater import Updater
    import config
    updater = Updater(config.APP_VERSION, config.GITHUB_REPO)
    result = updater.check_and_update()
    if result == "updated":
        return
    elif result == "failed":
        import tkinter as tk
        from tkinter import messagebox
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showwarning(
            "업데이트 확인 실패",
            "최신 버전 확인에 실패했습니다.\n\n"
            "인터넷 연결을 확인하시거나\n"
            "전산팀에 연락해주세요.\n\n"
            "확인을 누르면 현재 버전으로 실행됩니다.",
        )
        _root.destroy()

    # pywebview 앱 시작
    import webview
    from ui.webview_api import WebViewAPI

    api = WebViewAPI()
    window = webview.create_window(
        f"{config.APP_NAME} v{config.APP_VERSION}",
        _html_path(),
        js_api=api,
        width=config.APP_WIDTH,
        height=config.APP_HEIGHT,
        min_size=(config.MIN_WIDTH, config.MIN_HEIGHT),
        resizable=True,
    )
    api.set_window(window)
    webview.start()


if __name__ == "__main__":
    main()
