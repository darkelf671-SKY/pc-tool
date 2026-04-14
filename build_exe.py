"""PyInstaller 빌드 스크립트"""

import PyInstaller.__main__
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(BASE_DIR, "main.py"),
    "--onefile",
    "--windowed",
    "--name", "PC문제해결도우미",
    # 데이터 파일
    "--add-data", f"{os.path.join(BASE_DIR, 'data', 'symptom_map.json')};data",
    "--add-data", f"{os.path.join(BASE_DIR, 'ui', 'index.html')};ui",
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
    # 관리자 권한
    "--uac-admin",
    "--clean",
    "--noconfirm",
])
