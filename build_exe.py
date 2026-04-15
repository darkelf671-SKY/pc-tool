"""PyInstaller 빌드 스크립트"""

import PyInstaller.__main__
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.dirname(sys.executable)
TCL_DIR = os.path.join(PYTHON_DIR, "tcl", "tcl8.6")
TK_DIR = os.path.join(PYTHON_DIR, "tcl", "tk8.6")

PyInstaller.__main__.run([
    os.path.join(BASE_DIR, "main.py"),
    "--onefile",
    "--windowed",
    "--name", "PC문제해결도우미",
    # 데이터 파일
    "--add-data", f"{os.path.join(BASE_DIR, 'data', 'symptom_map.json')};data",
    "--add-data", f"{os.path.join(BASE_DIR, 'ui', 'index.html')};ui",
    # Tcl/Tk 데이터 (PyInstaller 번들링 누락 방지)
    "--add-data", f"{TCL_DIR};tcl8.6",
    "--add-data", f"{TK_DIR};tk8.6",
    # 모든 도구 모듈
    "--hidden-import", "tools.printer_spooler",
    "--hidden-import", "tools.winupdate_cache",
    "--hidden-import", "tools.browser_reset",
    "--hidden-import", "tools.dns_flush",
    "--hidden-import", "tools.network_reset",
    "--hidden-import", "tools.temp_cleanup",
    "--hidden-import", "tools.explorer_restart",
    "--hidden-import", "tools.store_app_reset",
    "--hidden-import", "tools.icon_cache",
    "--hidden-import", "tools.sfc_scan",
    "--hidden-import", "tools.remote_support",
    "--hidden-import", "tools.ime_fix",
    "--hidden-import", "tools.ms_account_cleanup",
    "--hidden-import", "tools.teams_reinstall",
    "--hidden-import", "tools.his_reinstall",
    "--hidden-import", "tools.banking_reset",
    # pywebview + pythonnet 의존성
    "--hidden-import", "_cffi_backend",
    "--hidden-import", "clr_loader",
    "--hidden-import", "clr_loader.ffi",
    "--hidden-import", "clr_loader.netfx",
    "--hidden-import", "clr_loader.hostfxr",
    "--hidden-import", "pythonnet",
    # 관리자 권한
    "--uac-admin",
    "--clean",
    "--noconfirm",
])
