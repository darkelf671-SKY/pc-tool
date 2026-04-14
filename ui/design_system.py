"""디자인 시스템 — 서울재활병원 브랜드 컬러, 폰트, 스타일"""

import tkinter as tk
from tkinter import ttk

COLORS = {
    "brand": "#65BB00",
    "brand_dark": "#58A201",
    "brand_light": "#E8F5D6",
    "brand_bg": "#F4FAE8",
    "navy": "#1E2C67",
    "danger": "#E40214",
    "danger_light": "#FDE8EA",
    "warning": "#F5A623",
    "warning_light": "#FFF5E0",
    "warning_border": "#F5D89A",
    "warning_text": "#92400E",
    "blue": "#008FC3",
    "blue_light": "#E0F4FB",
    "purple": "#7C3AED",
    "purple_light": "#F3E8FF",
    "white": "#FFFFFF",
    "gray_50": "#FAFBFC",
    "gray_100": "#F6F6F6",
    "gray_200": "#EEEEEE",
    "gray_300": "#DDDDDD",
    "gray_400": "#AAAAAA",
    "gray_500": "#888888",
    "gray_600": "#666666",
    "gray_700": "#444444",
    "gray_800": "#333333",
    "gray_900": "#111111",
    "terminal_bg": "#1A1A2E",
    "terminal_text": "#A5F3A3",
    "terminal_time": "#64748B",
}

FONTS = {
    "title_lg": ("맑은 고딕", 18, "bold"),
    "heading": ("맑은 고딕", 16, "bold"),
    "subheading": ("맑은 고딕", 13, "bold"),
    "body": ("맑은 고딕", 11),
    "body_bold": ("맑은 고딕", 11, "bold"),
    "small": ("맑은 고딕", 10),
    "small_bold": ("맑은 고딕", 10, "bold"),
    "tag": ("맑은 고딕", 9),
    "tag_bold": ("맑은 고딕", 9, "bold"),
    "mono": ("Consolas", 9),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "xxl": 24,
}

# 스크롤 영역 배경 (목업의 body 배경)
BG_SURFACE = "#F0F2F5"

# 증상별 솔루션 아이콘 매핑 (목업 기준)
SOLUTION_ICON_MAP = {
    # (icon_emoji, icon_bg_color)
    "printer_stuck": ("🔄", "brand_light"),
    "site_blocked": ("🔌", "brand_light"),
    "ssl_warning": ("🌐", "blue_light"),
    "connected_but_no": ("📡", "warning_light"),
    "slow_boot": ("🗑️", "brand_light"),
    "taskbar_frozen": ("📁", "blue_light"),
    "random_errors": ("🔧", "warning_light"),
    "teams_broken": ("💬", "brand_light"),
    "browser_broken": ("🌐", "blue_light"),
    "emr_broken": ("🏥", "warning_light"),
    "outlook_store_broken": ("📦", "gray_100"),
    "ime_spacing": ("⌨️", "brand_light"),
    "update_fail": ("🔄", "brand_light"),
    "icon_broken": ("🖼️", "brand_light"),
    "taskbar_gone": ("📁", "blue_light"),
    "ms_account_error": ("🔑", "brand_light"),
    "ms_login_0x_error": ("⚠️", "blue_light"),
    "outlook_other_account": ("💼", "gray_100"),
}

# 전체도구 아이콘+설명 매핑 (목업 기준)
TOOL_DISPLAY_MAP = {
    "printer_spooler": ("🖨️", "프린터 초기화", "인쇄 대기열 비우기"),
    "winupdate_cache": ("🔄", "업데이트 캐시", "업데이트 오류 해결"),
    "browser_reset": ("🌐", "브라우저 초기화", "캐시/쿠키/SSL 정리"),
    "dns_flush": ("🔌", "DNS 초기화", "사이트 접속 오류"),
    "network_reset": ("📡", "네트워크 초기화", "인터넷 연결 복구"),
    "temp_cleanup": ("🗑️", "임시파일 정리", "디스크 공간 확보"),
    "explorer_restart": ("📁", "탐색기 재시작", "작업표시줄 복구"),
    "store_app_reset": ("📦", "Store 앱 초기화", "Outlook 등 앱 복구"),
    "icon_cache": ("🖼️", "아이콘 캐시", "깨진 아이콘 복구"),
    "sfc_scan": ("🔧", "시스템 파일 검사", "SFC + DISM 복구"),
    "ms_account_cleanup": ("🔑", "MS 계정 초기화", "이전 계정 정리"),
    "ime_fix": ("⌨️", "입력기 복구", "글자 간격/IME 오류"),
    "remote_support": ("📞", "원격 지원 요청", "전산팀 원격 도움"),
}


def apply_theme(root: tk.Tk):
    """ttk 스타일 일괄 적용"""
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=COLORS["white"])
    style.configure(".", font=FONTS["body"], background=COLORS["white"])

    style.configure(
        "Brand.TButton",
        background=COLORS["brand"],
        foreground=COLORS["white"],
        font=FONTS["body_bold"],
        padding=(16, 8),
        borderwidth=0,
    )
    style.map(
        "Brand.TButton",
        background=[("active", COLORS["brand_dark"])],
    )

    style.configure(
        "Danger.TButton",
        background=COLORS["danger"],
        foreground=COLORS["white"],
        font=FONTS["body_bold"],
        padding=(16, 8),
        borderwidth=0,
    )

    style.configure(
        "Secondary.TButton",
        background=COLORS["gray_200"],
        foreground=COLORS["gray_800"],
        font=FONTS["body"],
        padding=(16, 8),
        borderwidth=0,
    )
