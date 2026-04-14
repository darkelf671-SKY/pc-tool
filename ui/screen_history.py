"""실행 기록 화면 (목업 동일)"""

import tkinter as tk
from ui.design_system import COLORS, FONTS, SPACING, BG_SURFACE, TOOL_DISPLAY_MAP
from core.logger import ToolLogger


class ScreenHistory(tk.Frame):
    def __init__(self, parent, logger: ToolLogger):
        super().__init__(parent, bg=COLORS["white"])
        self._logger = logger
        self._content = None
        self.refresh()

    def refresh(self):
        if self._content:
            self._content.destroy()

        self._content = tk.Frame(self, bg=COLORS["white"])
        self._content.pack(fill="both", expand=True)

        canvas = tk.Canvas(self._content, bg=COLORS["white"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self._content, orient="vertical", command=canvas.yview)
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

        entries = self._logger.get_recent(30)

        if not entries:
            # 빈 상태 (목업 스타일)
            empty = tk.Frame(inner, bg=COLORS["white"])
            empty.pack(fill="both", expand=True, pady=60)
            tk.Label(
                empty, text="📋", font=("Segoe UI Emoji", 40),
                bg=COLORS["white"],
            ).pack()
            tk.Label(
                empty, text="아직 실행 기록이 없어요",
                font=FONTS["body_bold"], bg=COLORS["white"],
                fg=COLORS["gray_400"],
            ).pack(pady=(12, 4))
            tk.Label(
                empty, text="도구를 실행하면 여기에 기록됩니다",
                font=FONTS["small"], bg=COLORS["white"],
                fg=COLORS["gray_400"],
            ).pack()
            return

        # 기록 목록 (목업: .history-item, bottom dividers only)
        list_area = tk.Frame(inner, bg=COLORS["white"])
        list_area.pack(fill="x")

        for entry in entries:
            self._create_history_item(list_area, entry)

    def _create_history_item(self, parent, entry: dict):
        """목업: .history-item — 하단 구분선만, 카드 테두리 없음"""
        item = tk.Frame(parent, bg=COLORS["white"], cursor="hand2")
        item.pack(fill="x")

        inner = tk.Frame(item, bg=COLORS["white"], padx=16, pady=14)
        inner.pack(fill="x")

        # 좌측: 아이콘 + 텍스트 (목업: .history-left)
        left = tk.Frame(inner, bg=COLORS["white"])
        left.pack(side="left", fill="x", expand=True)

        success = entry.get("success", False)
        tool_id = entry.get("tool_id", "")

        # 36x36 아이콘 (목업: .history-icon)
        icon_bg = COLORS["brand_light"] if success else COLORS["danger_light"]
        icon_emoji = "✅" if success else "❌"
        # 도구별 아이콘 사용
        tool_info = TOOL_DISPLAY_MAP.get(tool_id)
        if tool_info:
            icon_emoji = tool_info[0]

        icon_frame = tk.Frame(left, bg=icon_bg, width=36, height=36)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        tk.Label(
            icon_frame, text=icon_emoji,
            font=("Segoe UI Emoji", 14), bg=icon_bg,
        ).pack(expand=True)

        # 텍스트
        text_area = tk.Frame(left, bg=COLORS["white"])
        text_area.pack(side="left", padx=(12, 0))

        # 도구명 (목업: .history-name)
        tk.Label(
            text_area, text=entry.get("tool_name", ""),
            font=(FONTS["body_bold"][0], 12, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_800"], anchor="w",
        ).pack(anchor="w")

        # 증상 (목업: .history-desc)
        symptom = entry.get("symptom_title", "")
        if len(symptom) > 35:
            symptom = symptom[:34] + "..."
        tk.Label(
            text_area, text=symptom,
            font=FONTS["tag"], bg=COLORS["white"],
            fg=COLORS["gray_500"], anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # 우측: 상태 + 날짜 (목업: .history-right)
        right = tk.Frame(inner, bg=COLORS["white"])
        right.pack(side="right")

        status_text = "성공" if success else "실패"
        status_fg = COLORS["brand_dark"] if success else COLORS["danger"]
        tk.Label(
            right, text=status_text,
            font=FONTS["tag_bold"], bg=COLORS["white"],
            fg=status_fg, anchor="e",
        ).pack(anchor="e")

        ts = entry.get("timestamp", "")[:16].replace("T", " ")
        tk.Label(
            right, text=ts,
            font=FONTS["tag"], bg=COLORS["white"],
            fg=COLORS["gray_400"], anchor="e",
        ).pack(anchor="e", pady=(2, 0))

        # 하단 구분선 (목업: border-bottom:1px solid gray-100)
        tk.Frame(item, bg=COLORS["gray_100"], height=1).pack(fill="x", padx=16)

        # 호버 (목업: background:gray-50)
        def on_enter(e):
            inner.configure(bg=COLORS["gray_50"])
            left.configure(bg=COLORS["gray_50"])
            text_area.configure(bg=COLORS["gray_50"])
            right.configure(bg=COLORS["gray_50"])
        def on_leave(e):
            inner.configure(bg=COLORS["white"])
            left.configure(bg=COLORS["white"])
            text_area.configure(bg=COLORS["white"])
            right.configure(bg=COLORS["white"])
        for w in [item, inner]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
