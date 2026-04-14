"""메인 윈도우 — 화면 전환 + 네비게이션 (목업 동일 구조)"""

import json
import os
import sys
import tkinter as tk
from tkinter import messagebox
import webbrowser

import config
from ui.design_system import COLORS, FONTS, SPACING, apply_theme
from ui.screen_home import ScreenHome
from ui.screen_detail import ScreenDetail
from ui.screen_alltools import ScreenAllTools
from ui.screen_history import ScreenHistory
from ui.screen_guide import ScreenGuide
from ui.dialog_confirm import ConfirmDialog
from ui.dialog_exec import ExecDialog
from ui.dialog_result import ResultDialog
from tools.registry import get_tool
from core.logger import ToolLogger


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.geometry(f"{config.APP_WIDTH}x{config.APP_HEIGHT}")
        self.minsize(config.MIN_WIDTH, config.MIN_HEIGHT)
        self.resizable(False, True)
        self.configure(bg=COLORS["white"])

        apply_theme(self)

        self._logger = ToolLogger(self._resolve_path(config.LOG_DIR))
        self._symptom_map = self._load_symptom_map()

        # 목업 순서: Header → Remote Banner → Nav Tabs → Content
        self._build_header()
        self._build_remote_banner()
        self._build_nav_tabs()
        self._build_container()
        self._create_screens()
        self.show_screen("home")

    # ── 데이터 ──

    def _resolve_path(self, rel_path: str) -> str:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, rel_path)

    def _load_symptom_map(self) -> dict:
        path = self._resolve_path(config.SYMPTOM_MAP_FILE)
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] symptom_map.json 로드 실패: {e}")
            return self._default_map()

    def _default_map(self) -> dict:
        return {
            "version": "fallback",
            "remote_support": {
                "url": config.REMOTE_SUPPORT_URL,
                "label": "원격 지원 요청",
                "description": "JSON 로드에 실패했습니다. 전산팀에 문의하세요.",
            },
            "categories": [],
            "tag_labels": {},
        }

    # ── 헤더 (목업: .header) ──

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["white"])
        header.pack(fill="x")

        # 목업: .header-top — padding:14px 20px
        top = tk.Frame(header, bg=COLORS["white"])
        top.pack(fill="x", padx=20, pady=14)

        # 목업: .header-left — logo + divider + title
        left = tk.Frame(top, bg=COLORS["white"])
        left.pack(side="left")

        tk.Label(
            left, text="🏥", font=("Segoe UI Emoji", 18),
            bg=COLORS["white"],
        ).pack(side="left")

        # 목업: .header-divider — 1px x 24px
        divider = tk.Frame(left, bg=COLORS["gray_300"], width=1, height=24)
        divider.pack(side="left", padx=12)
        divider.pack_propagate(False)

        title_area = tk.Frame(left, bg=COLORS["white"])
        title_area.pack(side="left")

        # 목업: .header-title — 16px bold
        tk.Label(
            title_area, text=config.APP_NAME,
            font=("맑은 고딕", 14, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_900"],
        ).pack(anchor="w")

        # 목업: .header-ver — 11px gray-500
        tk.Label(
            title_area, text=f"v{config.APP_VERSION}",
            font=FONTS["tag"], bg=COLORS["white"],
            fg=COLORS["gray_500"],
        ).pack(anchor="w")

        # 목업: .header-accent — 3px gradient bar
        accent = tk.Frame(header, bg=COLORS["brand"], height=3)
        accent.pack(fill="x")

    # ── 원격 지원 배너 (목업: .remote-banner) ──

    def _build_remote_banner(self):
        rs = self._symptom_map.get("remote_support", {})

        # 목업: padding:10px 20px, border-bottom:1px gray-200
        banner = tk.Frame(self, bg=COLORS["white"])
        banner.pack(fill="x")

        inner = tk.Frame(banner, bg=COLORS["white"], padx=20, pady=10)
        inner.pack(fill="x")

        # 목업: .remote-banner-left
        left = tk.Frame(inner, bg=COLORS["white"])
        left.pack(side="left")

        # 목업: .remote-dot — 8px green circle
        dot = tk.Canvas(left, width=10, height=10, bg=COLORS["white"],
                        highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=COLORS["brand"], outline="")
        dot.pack(side="left")

        # 목업: .remote-banner-text
        tk.Label(
            left, text="  해결이 어려우시면 ",
            font=FONTS["small"], bg=COLORS["white"],
            fg=COLORS["gray_600"],
        ).pack(side="left")
        tk.Label(
            left, text="전산팀 원격 지원",
            font=FONTS["small_bold"], bg=COLORS["white"],
            fg=COLORS["gray_800"],
        ).pack(side="left")

        # 목업: .remote-btn — danger bg, pill, 12px bold
        url = rs.get("url", config.REMOTE_SUPPORT_URL)
        btn = tk.Label(
            inner, text=" 📞 원격 지원 요청 ",
            font=FONTS["small_bold"], bg=COLORS["danger"],
            fg=COLORS["white"], padx=16, pady=7, cursor="hand2",
        )
        btn.pack(side="right")
        btn.bind("<Button-1>", lambda e: webbrowser.open(url))

        def _btn_enter(e):
            btn.configure(bg="#C50110")
        def _btn_leave(e):
            btn.configure(bg=COLORS["danger"])
        btn.bind("<Enter>", _btn_enter)
        btn.bind("<Leave>", _btn_leave)

        # 하단 구분선
        tk.Frame(banner, bg=COLORS["gray_200"], height=1).pack(fill="x")

    # ── 네비게이션 탭 (목업: .nav-tabs — 상단, 헤더 바로 아래) ──

    def _build_nav_tabs(self):
        nav = tk.Frame(self, bg=COLORS["white"])
        nav.pack(fill="x")

        self._nav_btns: dict[str, dict] = {}

        # 목업: 🏠 문제 찾기 / 🧰 전체 도구 / 📋 실행 기록 / ℹ️ 사용법
        tabs = [
            ("home", "🏠", "문제 찾기"),
            ("alltools", "🧰", "전체 도구"),
            ("history", "📋", "실행 기록"),
            ("guide", "ℹ️", "사용법"),
        ]
        for name, icon, label in tabs:
            btn = tk.Frame(nav, bg=COLORS["white"], cursor="hand2")
            btn.pack(side="left", fill="both", expand=True)

            # 목업: .nav-tab — column layout
            icon_lbl = tk.Label(
                btn, text=icon, font=("Segoe UI Emoji", 16),
                bg=COLORS["white"],
            )
            icon_lbl.pack(pady=(10, 0))

            text_lbl = tk.Label(
                btn, text=label, font=FONTS["tag"],
                bg=COLORS["white"], fg=COLORS["gray_500"],
            )
            text_lbl.pack(pady=(2, 8))

            # 목업: border-bottom:2px solid transparent → active: brand
            accent = tk.Frame(btn, bg=COLORS["white"], height=2)
            accent.pack(fill="x", side="bottom")

            def on_click(e, n=name):
                self.show_screen(n)
            for w in [btn, icon_lbl, text_lbl]:
                w.bind("<Button-1>", on_click)

            # 호버 (목업: .nav-tab:hover — brand-bg)
            def on_enter(e, b=btn, i=icon_lbl, t=text_lbl):
                b.configure(bg=COLORS["brand_bg"])
                i.configure(bg=COLORS["brand_bg"])
                t.configure(bg=COLORS["brand_bg"])
            def on_leave(e, b=btn, i=icon_lbl, t=text_lbl, n=name):
                bg = COLORS["white"]
                b.configure(bg=bg)
                i.configure(bg=bg)
                t.configure(bg=bg)

            for w in [btn, icon_lbl, text_lbl]:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)

            self._nav_btns[name] = {
                "frame": btn, "icon": icon_lbl, "text": text_lbl,
                "accent": accent,
            }

        # 하단 구분선
        tk.Frame(self, bg=COLORS["gray_200"], height=1).pack(fill="x")

    # ── 컨테이너 ──

    def _build_container(self):
        self._container = tk.Frame(self, bg=COLORS["white"])
        self._container.pack(fill="both", expand=True)

    # ── 화면 ──

    def _create_screens(self):
        self._screens: dict[str, tk.Frame] = {}

        self._screens["home"] = ScreenHome(
            self._container, self._symptom_map,
            on_category_click=self._go_to_detail,
        )
        self._screens["detail"] = ScreenDetail(
            self._container,
            on_back=lambda: self.show_screen("home"),
            on_symptom_click=self._on_symptom_click,
        )
        self._screens["alltools"] = ScreenAllTools(
            self._container, self._symptom_map,
            on_symptom_click=self._on_symptom_click,
        )
        self._screens["history"] = ScreenHistory(
            self._container, self._logger,
        )
        self._screens["guide"] = ScreenGuide(self._container)

        for screen in self._screens.values():
            screen.place(x=0, y=0, relwidth=1, relheight=1)

    def show_screen(self, name: str):
        screen = self._screens.get(name)
        if screen:
            if name == "history":
                screen.refresh()
            screen.tkraise()
        self._update_nav(name)

    def _update_nav(self, active: str):
        for name, widgets in self._nav_btns.items():
            if name == active:
                # 목업: .nav-tab.active — brand color, bottom border
                widgets["text"].configure(
                    fg=COLORS["brand"],
                    font=FONTS["small_bold"],
                )
                widgets["icon"].configure(fg=COLORS["brand"])
                widgets["accent"].configure(bg=COLORS["brand"])
            else:
                widgets["text"].configure(
                    fg=COLORS["gray_500"],
                    font=FONTS["tag"],
                )
                widgets["icon"].configure(fg=COLORS["gray_900"])
                widgets["accent"].configure(bg=COLORS["white"])

    # ── 화면 전환 ──

    def _go_to_detail(self, category_id: str):
        cat = None
        for c in self._symptom_map.get("categories", []):
            if c["id"] == category_id:
                cat = c
                break
        if cat:
            tag_labels = self._symptom_map.get("tag_labels", {})
            self._screens["detail"].show_category(cat, tag_labels)
            self.show_screen("detail")

    def _on_symptom_click(self, symptom: dict):
        """증상 카드 [실행하기] 클릭 → 확인 다이얼로그"""
        tool_id = symptom.get("tool_id", "")
        tool = get_tool(tool_id)
        if not tool:
            messagebox.showerror(
                "오류", f"도구를 찾을 수 없습니다: {tool_id}",
            )
            return

        if symptom.get("confirm_steps"):
            ConfirmDialog(self, symptom, on_confirm=self._execute_tool)
        else:
            self._execute_tool(symptom)

    def _execute_tool(self, symptom: dict):
        tool_id = symptom.get("tool_id", "")
        tool = get_tool(tool_id)
        if not tool:
            return

        ExecDialog(
            self, symptom, tool,
            on_complete=self._on_tool_complete,
        )

    def _on_tool_complete(self, symptom: dict, success: bool, duration: float):
        tool_id = symptom.get("tool_id", "")
        tool = get_tool(tool_id)
        tool_name = tool.name if tool else tool_id

        self._logger.log_execution(
            tool_id=tool_id,
            tool_name=tool_name,
            symptom_title=symptom.get("title", ""),
            success=success,
            duration_sec=duration,
        )

        ResultDialog(self, symptom, success, duration)
