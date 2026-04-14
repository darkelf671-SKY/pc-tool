"""전체 도구 화면 — 목업 동일 (섹션 레이블 + 3열 그리드)"""

import tkinter as tk
import webbrowser
from ui.design_system import COLORS, FONTS, SPACING, BG_SURFACE, TOOL_DISPLAY_MAP
from tools.registry import TOOL_REGISTRY
import config


class ScreenAllTools(tk.Frame):
    def __init__(self, parent, symptom_map: dict, on_symptom_click):
        super().__init__(parent, bg=COLORS["white"])
        self._map = symptom_map
        self._on_click = on_symptom_click
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=COLORS["white"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLORS["white"])
        inner.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 도구 분류 (목업 기준)
        basic_ids = [
            "printer_spooler", "winupdate_cache", "browser_reset",
            "dns_flush", "network_reset", "temp_cleanup",
        ]
        advanced_ids = [
            "explorer_restart", "store_app_reset", "icon_cache",
            "sfc_scan", "ms_account_cleanup", "ime_fix",
        ]

        # v1.0 도구를 symptom에서 가져오기 (클릭 이벤트용)
        symptom_by_tool: dict = {}
        v11_symptoms = []
        for cat in self._map.get("categories", []):
            for s in cat.get("symptoms", []):
                tid = s.get("tool_id", "")
                if "v1.1" in s.get("tags", []):
                    v11_symptoms.append(s)
                elif tid:
                    symptom_by_tool[tid] = s

        pad = SPACING["xl"]

        # ── 기본 도구 (목업: .section-label + .all-tools-grid)
        self._section_label(inner, "기본 도구", pad, first=True)
        grid1 = tk.Frame(inner, bg=COLORS["white"])
        grid1.pack(fill="x", padx=pad)
        for i, tid in enumerate(basic_ids):
            self._mini_card(grid1, tid, symptom_by_tool.get(tid), i)
        grid1.columnconfigure(0, weight=1)
        grid1.columnconfigure(1, weight=1)
        grid1.columnconfigure(2, weight=1)

        # ── 고급 도구
        self._section_label(inner, "고급 도구", pad)
        grid2 = tk.Frame(inner, bg=COLORS["white"])
        grid2.pack(fill="x", padx=pad)
        for i, tid in enumerate(advanced_ids):
            self._mini_card(grid2, tid, symptom_by_tool.get(tid), i)
        grid2.columnconfigure(0, weight=1)
        grid2.columnconfigure(1, weight=1)
        grid2.columnconfigure(2, weight=1)

        # ── v1.1 도구
        if v11_symptoms:
            self._section_label(inner, "v1.1 도구", pad)
            grid3 = tk.Frame(inner, bg=COLORS["white"])
            grid3.pack(fill="x", padx=pad)
            for i, s in enumerate(v11_symptoms):
                self._mini_card_v11(grid3, s, i)
            grid3.columnconfigure(0, weight=1)
            grid3.columnconfigure(1, weight=1)
            grid3.columnconfigure(2, weight=1)

        # ── 지원 (목업: grid-column:span 3, border-color:danger)
        self._section_label(inner, "지원", pad)
        support_frame = tk.Frame(inner, bg=COLORS["white"])
        support_frame.pack(fill="x", padx=pad, pady=(0, SPACING["xl"]))

        support_card = tk.Frame(
            support_frame, bg=COLORS["white"],
            highlightbackground=COLORS["danger"], highlightthickness=1,
            cursor="hand2",
        )
        support_card.pack(fill="x")

        sup_inner = tk.Frame(support_card, bg=COLORS["white"], padx=8, pady=14)
        sup_inner.pack(fill="both", expand=True)

        tk.Label(
            sup_inner, text="📞", font=("Segoe UI Emoji", 20),
            bg=COLORS["white"],
        ).pack()
        tk.Label(
            sup_inner, text="원격 지원 요청 (367.co.kr)",
            font=FONTS["small_bold"], bg=COLORS["white"],
            fg=COLORS["gray_800"],
        ).pack(pady=(4, 0))
        tk.Label(
            sup_inner, text="전산팀이 원격으로 도와드립니다",
            font=FONTS["tag"], bg=COLORS["white"],
            fg=COLORS["gray_500"],
        ).pack(pady=(2, 0))

        def _open_remote(e):
            webbrowser.open(config.REMOTE_SUPPORT_URL)
        for w in [support_card, sup_inner]:
            w.bind("<Button-1>", _open_remote)

    def _section_label(self, parent, text: str, padx: int, first: bool = False):
        """목업: .section-label — 좌측 3px brand 바 + 텍스트"""
        frame = tk.Frame(parent, bg=COLORS["white"])
        frame.pack(fill="x", padx=padx,
                   pady=(SPACING["sm"] if first else SPACING["xl"], SPACING["sm"]))

        # 좌측 3px 바
        bar = tk.Frame(frame, bg=COLORS["brand"], width=3, height=14)
        bar.pack(side="left")
        bar.pack_propagate(False)

        tk.Label(
            frame, text=text,
            font=(FONTS["tag_bold"][0], 10, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_500"],
        ).pack(side="left", padx=(8, 0))

    def _mini_card(self, parent, tool_id: str, symptom: dict | None, index: int):
        """목업: .mini-card — emoji + name + desc"""
        emoji, name, desc = TOOL_DISPLAY_MAP.get(
            tool_id, ("🔧", tool_id, ""),
        )

        card = tk.Frame(
            parent, bg=COLORS["white"],
            highlightbackground=COLORS["gray_200"], highlightthickness=1,
            cursor="hand2" if symptom else "arrow",
        )
        row, col = divmod(index, 3)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        inner = tk.Frame(card, bg=COLORS["white"], padx=8, pady=14)
        inner.pack(fill="both", expand=True)

        # 아이콘 (목업: 24px emoji)
        icon_lbl = tk.Label(
            inner, text=emoji, font=("Segoe UI Emoji", 20),
            bg=COLORS["white"],
        )
        icon_lbl.pack()

        # 이름 (목업: .mn, 11px bold)
        tk.Label(
            inner, text=name,
            font=FONTS["small_bold"], bg=COLORS["white"],
            fg=COLORS["gray_800"],
        ).pack(pady=(6, 0))

        # 설명 (목업: .md, 10px gray-500)
        tk.Label(
            inner, text=desc,
            font=FONTS["tag"], bg=COLORS["white"],
            fg=COLORS["gray_500"],
        ).pack(pady=(2, 0))

        if symptom:
            def on_click(e, s=symptom):
                self._on_click(s)

            def on_enter(e):
                card.configure(highlightbackground=COLORS["brand"])
                card.configure(bg=COLORS["brand_bg"])
                inner.configure(bg=COLORS["brand_bg"])
            def on_leave(e):
                card.configure(highlightbackground=COLORS["gray_200"])
                card.configure(bg=COLORS["white"])
                inner.configure(bg=COLORS["white"])

            for w in [card, inner, icon_lbl]:
                w.bind("<Button-1>", on_click)
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)

    def _mini_card_v11(self, parent, symptom: dict, index: int):
        """v1.1 예정 카드 (비활성)"""
        card = tk.Frame(
            parent, bg=COLORS["gray_50"],
            highlightbackground=COLORS["gray_200"], highlightthickness=1,
        )
        row, col = divmod(index, 3)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        inner = tk.Frame(card, bg=COLORS["gray_50"], padx=8, pady=14)
        inner.pack(fill="both", expand=True)

        # 아이콘 (카테고리에서 가져오기)
        icon = "🔒"
        for cat in self._map.get("categories", []):
            for s in cat.get("symptoms", []):
                if s.get("id") == symptom.get("id"):
                    icon = cat.get("icon", "🔒")
                    break

        tk.Label(
            inner, text=icon, font=("Segoe UI Emoji", 20),
            bg=COLORS["gray_50"],
        ).pack()
        title = symptom.get("title", "")
        if len(title) > 10:
            title = title[:9] + "..."
        tk.Label(
            inner, text=title,
            font=FONTS["small_bold"], bg=COLORS["gray_50"],
            fg=COLORS["gray_400"],
        ).pack(pady=(6, 0))
        tk.Label(
            inner, text="v1.1 예정",
            font=FONTS["tag"], bg=COLORS["gray_50"],
            fg=COLORS["gray_400"],
        ).pack(pady=(2, 0))
