"""PC 문제해결 도우미 — 진입점 (pywebview)"""

import ctypes
import sys
import os


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


def _html_path() -> str:
    """index.html 경로 (EXE/개발 환경 대응)"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "ui", "index.html")


def main():
    set_dpi_awareness()
    ensure_admin()

    # 자동 업데이트 (UI 표시 전)
    from updater import Updater
    import config
    updater = Updater(config.APP_VERSION, config.GITHUB_REPO)
    if updater.check_and_update():
        return

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
