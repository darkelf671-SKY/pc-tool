"""홈 화면 — 증상 카테고리 그리드 (목업 동일)"""

import tkinter as tk
from ui.design_system import COLORS, FONTS, SPACING, BG_SURFACE


class ScreenHome(tk.Frame):
    def __init__(self, parent, symptom_map: dict, on_category_click):
        super().__init__(parent, bg=COLORS["white"])
        self._map = symptom_map
        self._on_click = on_category_click
        self._build()

    def _build(self):
        # 스크롤 영역
        canvas = tk.Canvas(self, bg=COLORS["white"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._inner = tk.Frame(canvas, bg=COLORS["white"])
        self._inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 인사말 (목업: h2 + p)
        greet = tk.Frame(self._inner, bg=COLORS["white"])
        greet.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xxl"], SPACING["sm"]))

        # "어떤 문제가 있으신가요?" — "문제" 부분 초록색
        title_row = tk.Frame(greet, bg=COLORS["white"])
        title_row.pack(anchor="w")
        tk.Label(
            title_row, text="어떤 ",
            font=FONTS["title_lg"], bg=COLORS["white"],
            fg=COLORS["gray_900"],
        ).pack(side="left")
        tk.Label(
            title_row, text="문제",
            font=FONTS["title_lg"], bg=COLORS["white"],
            fg=COLORS["brand"],
        ).pack(side="left")
        tk.Label(
            title_row, text="가 있으신가요?",
            font=FONTS["title_lg"], bg=COLORS["white"],
            fg=COLORS["gray_900"],
        ).pack(side="left")

        tk.Label(
            greet, text="증상을 선택하시면 해결 방법을 안내해드립니다",
            font=FONTS["small"], bg=COLORS["white"],
            fg=COLORS["gray_500"], anchor="w",
        ).pack(fill="x", pady=(6, 0))

        # 카테고리 그리드 (목업: 2열, gap 12px)
        grid = tk.Frame(self._inner, bg=COLORS["white"])
        grid.pack(fill="both", expand=True, padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["lg"]))

        categories = sorted(
            [c for c in self._map.get("categories", [])
             if c.get("visible", True)],
            key=lambda c: c.get("order", 99),
        )

        for i, cat in enumerate(categories):
            card = self._create_card(grid, cat)
            row, col = divmod(i, 2)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def _create_card(self, parent, cat: dict) -> tk.Frame:
        cid = cat["id"]
        symptoms = [s for s in cat.get("symptoms", [])
                     if s.get("visible", True)]
        count = len(symptoms)

        # 계정 카테고리는 highlight (초록 테두리)
        border_color = COLORS["brand"] if cid == "account" else COLORS["gray_200"]
        border_width = 2 if cid == "account" else 1

        card = tk.Frame(
            parent, bg=COLORS["white"],
            highlightbackground=border_color,
            highlightthickness=border_width,
            cursor="hand2",
        )
        card.configure(padx=16, pady=20)

        # NEW 배지 (계정 카테고리)
        if cid == "account":
            new_badge = tk.Label(
                card, text=" NEW ",
                font=FONTS["tag_bold"], bg=COLORS["brand"],
                fg=COLORS["white"], padx=6, pady=1,
            )
            new_badge.place(relx=1.0, y=2, anchor="ne")

        # 아이콘 (목업: 36px emoji 직접 표시, 원형 배경 없음)
        icon_lbl = tk.Label(
            card, text=cat.get("icon", "🔧"),
            font=("Segoe UI Emoji", 28), bg=COLORS["white"],
        )
        icon_lbl.pack()

        # 카테고리 제목
        title = tk.Label(
            card, text=cat["title"],
            font=("맑은 고딕", 13, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_900"], wraplength=160,
        )
        title.pack(pady=(10, 4))

        # 설명
        desc = tk.Label(
            card, text=cat.get("description", ""),
            font=FONTS["tag"], bg=COLORS["white"],
            fg=COLORS["gray_500"], wraplength=160,
        )
        desc.pack()

        # 도구 개수 배지 (목업: pill, brand-bg)
        badge = tk.Label(
            card, text=f"해결 도구 {count}개",
            font=FONTS["tag_bold"], bg=COLORS["brand_bg"],
            fg=COLORS["brand_dark"], padx=10, pady=3,
        )
        badge.pack(pady=(10, 0))

        # 클릭 이벤트
        def on_click(e, _cid=cid):
            self._on_click(_cid)

        all_widgets = [card, icon_lbl, title, desc, badge]
        for widget in all_widgets:
            widget.bind("<Button-1>", on_click)

        # 호버 효과 (목업: border-color brand)
        def on_enter(e):
            card.configure(highlightbackground=COLORS["brand"])
        def on_leave(e):
            card.configure(
                highlightbackground=border_color,
            )

        for widget in all_widgets:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return card
