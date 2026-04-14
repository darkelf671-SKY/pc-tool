"""상세 화면 — 세부 증상 목록 (목업 동일)"""

import tkinter as tk
from ui.design_system import (
    COLORS, FONTS, SPACING, BG_SURFACE, SOLUTION_ICON_MAP,
)


# 태그 색상 매핑 (목업 기준)
TAG_COLORS = {
    "safe":    (COLORS["brand_light"], COLORS["brand_dark"]),   # .tag.safe
    "reboot":  (COLORS["warning_light"], "#B45309"),            # .tag.reboot
    "slow":    (COLORS["purple_light"], COLORS["purple"]),      # .tag.slow
    "instant": (COLORS["blue_light"], COLORS["blue"]),          # .tag.instant
}


class ScreenDetail(tk.Frame):
    def __init__(self, parent, on_back, on_symptom_click):
        super().__init__(parent, bg=BG_SURFACE)
        self._on_back = on_back
        self._on_symptom_click = on_symptom_click
        self._content = None
        self._tag_labels: dict = {}

    def show_category(self, category: dict, tag_labels: dict):
        """카테고리 데이터로 화면 재구성"""
        self._tag_labels = tag_labels
        if self._content:
            self._content.destroy()

        self._content = tk.Frame(self, bg=COLORS["white"])
        self._content.pack(fill="both", expand=True)

        # 스크롤
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

        # 뒤로가기 (목업: .detail-back)
        back_btn = tk.Label(
            inner, text="<  뒤로가기", font=FONTS["small_bold"],
            fg=COLORS["gray_500"], bg=COLORS["white"], cursor="hand2",
        )
        back_btn.pack(anchor="w", padx=SPACING["xl"], pady=(SPACING["lg"], SPACING["sm"]))
        back_btn.bind("<Button-1>", lambda e: self._on_back())

        def _back_enter(e):
            back_btn.configure(fg=COLORS["brand"])
        def _back_leave(e):
            back_btn.configure(fg=COLORS["gray_500"])
        back_btn.bind("<Enter>", _back_enter)
        back_btn.bind("<Leave>", _back_leave)

        # 카테고리 헤더 (목업: .detail-header)
        header = tk.Frame(inner, bg=COLORS["white"])
        header.pack(fill="x", padx=SPACING["xl"], pady=(0, SPACING["lg"]))

        tk.Label(
            header, text=category.get("icon", ""),
            font=("Segoe UI Emoji", 26), bg=COLORS["white"],
        ).pack(side="left")

        htext = tk.Frame(header, bg=COLORS["white"])
        htext.pack(side="left", padx=(14, 0))
        tk.Label(
            htext, text=category["title"],
            font=(FONTS["heading"][0], 17, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_900"],
        ).pack(anchor="w")
        tk.Label(
            htext, text="증상에 맞는 해결 방법을 선택하세요",
            font=FONTS["small"], bg=COLORS["white"], fg=COLORS["gray_500"],
        ).pack(anchor="w", pady=(2, 0))

        # 구분선 (목업: border-bottom:1px solid gray-200)
        tk.Frame(inner, bg=COLORS["gray_200"], height=1).pack(
            fill="x", padx=SPACING["xl"],
        )

        # 증상 카드들 (목업: padding:20px)
        cards_area = tk.Frame(inner, bg=COLORS["white"])
        cards_area.pack(fill="both", expand=True,
                        padx=SPACING["xl"], pady=(SPACING["lg"], 0))

        symptoms = [s for s in category.get("symptoms", [])
                     if s.get("visible", True)]
        for symptom in symptoms:
            self._create_solution_card(cards_area, symptom)

        # 팁 박스 (목업: .tip-box)
        tip_text = category.get("tip", "")
        if tip_text:
            self._create_tip_box(cards_area, tip_text)

    def _create_solution_card(self, parent, symptom: dict):
        """목업: .solution-card"""
        sid = symptom.get("id", "")

        # 카드 프레임 (목업: border:1px solid gray-200, border-radius:12px)
        card = tk.Frame(
            parent, bg=COLORS["white"],
            highlightbackground=COLORS["gray_200"], highlightthickness=1,
            cursor="hand2",
        )
        card.pack(fill="x", pady=(0, 10))

        inner = tk.Frame(card, bg=COLORS["white"], padx=18, pady=18)
        inner.pack(fill="x")

        # 상단: 아이콘 + 텍스트 (목업: .solution-top, flex, gap:14px)
        top = tk.Frame(inner, bg=COLORS["white"])
        top.pack(fill="x")

        # 44x44 컬러 아이콘 (목업: .solution-icon)
        icon_emoji, icon_bg_key = SOLUTION_ICON_MAP.get(
            sid, ("🔧", "brand_light"),
        )
        icon_bg = COLORS.get(icon_bg_key, COLORS["brand_light"])

        icon_frame = tk.Frame(top, bg=icon_bg, width=44, height=44)
        icon_frame.pack(side="left", anchor="n")
        icon_frame.pack_propagate(False)
        tk.Label(
            icon_frame, text=icon_emoji,
            font=("Segoe UI Emoji", 18), bg=icon_bg,
        ).pack(expand=True)

        # 텍스트 영역
        text_area = tk.Frame(top, bg=COLORS["white"])
        text_area.pack(side="left", fill="x", expand=True, padx=(14, 0))

        # 증상 제목 (목업: .si-symptom)
        tk.Label(
            text_area, text=symptom["title"],
            font=(FONTS["body_bold"][0], 12, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_900"], anchor="w", wraplength=340,
            justify="left",
        ).pack(fill="x")

        # 설명 (목업: .si-explain)
        explain = symptom.get("explain", "")
        if explain:
            tk.Label(
                text_area, text=explain,
                font=FONTS["small"], bg=COLORS["white"],
                fg=COLORS["gray_600"], anchor="w", wraplength=340,
                justify="left",
            ).pack(fill="x", pady=(4, 0))

        # 태그 (목업: .solution-tags)
        tags = symptom.get("tags", [])
        visible_tags = [t for t in tags if t != "v1.1"]
        if visible_tags:
            tag_frame = tk.Frame(text_area, bg=COLORS["white"])
            tag_frame.pack(fill="x", pady=(8, 0))
            for tag in visible_tags:
                label_text = self._tag_labels.get(tag, tag)
                bg_color, fg_color = self._get_tag_colors(tag)
                tk.Label(
                    tag_frame, text=f" {label_text} ",
                    font=FONTS["tag_bold"], bg=bg_color, fg=fg_color,
                    padx=8, pady=3,
                ).pack(side="left", padx=(0, 6))

        # 실행 버튼 (목업: .run-btn, border-radius:20px, 우측 정렬)
        btn_frame = tk.Frame(inner, bg=COLORS["white"])
        btn_frame.pack(fill="x", pady=(12, 0))

        run_btn = tk.Label(
            btn_frame, text="  ▶  실행하기  ",
            font=FONTS["body_bold"], bg=COLORS["brand"],
            fg=COLORS["white"], padx=20, pady=8, cursor="hand2",
        )
        run_btn.pack(anchor="e")

        # 실행 버튼 호버
        def on_btn_enter(e):
            run_btn.configure(bg=COLORS["brand_dark"])
        def on_btn_leave(e):
            run_btn.configure(bg=COLORS["brand"])
        run_btn.bind("<Enter>", on_btn_enter)
        run_btn.bind("<Leave>", on_btn_leave)

        # 클릭
        def on_click(e, s=symptom):
            self._on_symptom_click(s)
        run_btn.bind("<Button-1>", on_click)

        # 카드 호버 (목업: border-color:brand)
        def on_enter(e):
            card.configure(highlightbackground=COLORS["brand"])
        def on_leave(e):
            card.configure(highlightbackground=COLORS["gray_200"])
        for w in [card, inner, top, text_area]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def _create_tip_box(self, parent, text: str):
        """목업: .tip-box — brand-bg 배경, 좌측 3px brand 테두리"""
        # 외부 (좌측 액센트)
        outer = tk.Frame(parent, bg=COLORS["brand"])
        outer.pack(fill="x", pady=(6, SPACING["lg"]))

        tip = tk.Frame(outer, bg=COLORS["brand_bg"], padx=16, pady=14)
        tip.pack(fill="both", padx=(3, 0))  # 좌측 3px brand 바

        tk.Label(
            tip, text=text,
            font=FONTS["small"], bg=COLORS["brand_bg"],
            fg=COLORS["gray_700"], wraplength=400,
            justify="left", anchor="w",
        ).pack(fill="x")

    @staticmethod
    def _get_tag_colors(tag: str) -> tuple:
        """태그별 색상 반환 (목업 기준)"""
        if "no_reboot" in tag or tag == "safe":
            return TAG_COLORS["safe"]
        if tag == "reboot":
            return TAG_COLORS["reboot"]
        if "sec" in tag or "instant" in tag:
            return TAG_COLORS["instant"]
        if "slow" in tag or "min" in tag:
            return TAG_COLORS["slow"]
        return (COLORS["gray_100"], COLORS["gray_600"])
