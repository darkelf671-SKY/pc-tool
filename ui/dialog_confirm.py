"""실행 확인 다이얼로그 (목업 동일)"""

import tkinter as tk
from ui.design_system import COLORS, FONTS, SPACING, SOLUTION_ICON_MAP


class ConfirmDialog(tk.Toplevel):
    def __init__(self, parent, symptom: dict, on_confirm):
        super().__init__(parent)
        self.title("실행 전 확인")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=COLORS["white"])

        self._symptom = symptom
        self._on_confirm = on_confirm
        self._build()
        self._center(parent)

    def _build(self):
        f = tk.Frame(self, bg=COLORS["white"], padx=28, pady=28)
        f.pack(fill="both", expand=True)

        sid = self._symptom.get("id", "")

        # 중앙 아이콘 (목업: .cd-icon, 44px)
        icon_emoji, _ = SOLUTION_ICON_MAP.get(sid, ("🔧", "brand_light"))
        tk.Label(
            f, text=icon_emoji, font=("Segoe UI Emoji", 36),
            bg=COLORS["white"],
        ).pack()

        # 제목 (목업: .cd-title, 중앙)
        tk.Label(
            f, text=f"{self._symptom.get('title', '')}",
            font=(FONTS["subheading"][0], 14, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_900"], wraplength=360,
        ).pack(pady=(12, 6))

        # 설명 (목업: .cd-desc, 중앙)
        tk.Label(
            f, text="아래 작업을 자동으로 진행합니다",
            font=FONTS["body"], bg=COLORS["white"],
            fg=COLORS["gray_500"],
        ).pack(pady=(0, SPACING["xl"]))

        # 진행 단계 박스 (목업: .cd-what — gray-50, border)
        steps = self._symptom.get("confirm_steps", [])
        if steps:
            what_box = tk.Frame(
                f, bg=COLORS["gray_50"],
                highlightbackground=COLORS["gray_200"], highlightthickness=1,
            )
            what_box.pack(fill="x", pady=(0, SPACING["lg"]))

            what_inner = tk.Frame(what_box, bg=COLORS["gray_50"],
                                   padx=16, pady=16)
            what_inner.pack(fill="x")

            # 제목 (목업: .cd-what-title)
            tk.Label(
                what_inner, text="진행 단계",
                font=FONTS["tag_bold"], bg=COLORS["gray_50"],
                fg=COLORS["gray_500"], anchor="w",
            ).pack(fill="x", pady=(0, 8))

            # 단계 목록 (목업: .cd-what-list)
            for i, step in enumerate(steps, 1):
                row = tk.Frame(what_inner, bg=COLORS["gray_50"])
                row.pack(fill="x", pady=4)
                # 숫자 이모지
                nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
                num_icon = nums[i - 1] if i <= len(nums) else f"{i}."
                tk.Label(
                    row, text=num_icon,
                    font=("Segoe UI Emoji", 11), bg=COLORS["gray_50"],
                ).pack(side="left")
                tk.Label(
                    row, text=step,
                    font=FONTS["body"], bg=COLORS["gray_50"],
                    fg=COLORS["gray_700"], anchor="w",
                    wraplength=300, justify="left",
                ).pack(side="left", padx=(8, 0))

        # 경고 (목업: .cd-warn — warning-light, #F5D89A 테두리)
        warning = self._symptom.get("warning", "")
        if warning:
            warn_frame = tk.Frame(
                f, bg=COLORS["warning_light"],
                highlightbackground=COLORS["warning_border"],
                highlightthickness=1,
            )
            warn_frame.pack(fill="x", pady=(0, SPACING["lg"]))
            warn_inner = tk.Frame(warn_frame, bg=COLORS["warning_light"],
                                   padx=12, pady=12)
            warn_inner.pack(fill="x")
            tk.Label(
                warn_inner, text=f"⚠️  {warning}",
                font=FONTS["small"], bg=COLORS["warning_light"],
                fg=COLORS["warning_text"], wraplength=340,
                justify="left", anchor="w",
            ).pack(fill="x")

        # 버튼 (목업: .cd-btns — 2개 균등)
        btn_frame = tk.Frame(f, bg=COLORS["white"])
        btn_frame.pack(fill="x")

        # 취소 (목업: .cd-cancel — white bg, gray border)
        cancel_btn = tk.Label(
            btn_frame, text="취소",
            font=FONTS["body_bold"], bg=COLORS["white"],
            fg=COLORS["gray_700"], padx=24, pady=12, cursor="hand2",
            highlightbackground=COLORS["gray_300"], highlightthickness=1,
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        cancel_btn.bind("<Button-1>", lambda e: self.destroy())

        def _cancel_enter(e):
            cancel_btn.configure(bg=COLORS["gray_100"])
        def _cancel_leave(e):
            cancel_btn.configure(bg=COLORS["white"])
        cancel_btn.bind("<Enter>", _cancel_enter)
        cancel_btn.bind("<Leave>", _cancel_leave)

        # 실행 (목업: .cd-confirm — brand bg)
        run_btn = tk.Label(
            btn_frame, text="실행하기",
            font=FONTS["body_bold"], bg=COLORS["brand"],
            fg=COLORS["white"], padx=24, pady=12, cursor="hand2",
        )
        run_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        run_btn.bind("<Button-1>", self._on_run)

        def _run_enter(e):
            run_btn.configure(bg=COLORS["brand_dark"])
        def _run_leave(e):
            run_btn.configure(bg=COLORS["brand"])
        run_btn.bind("<Enter>", _run_enter)
        run_btn.bind("<Leave>", _run_leave)

    def _on_run(self, event):
        self.destroy()
        self._on_confirm(self._symptom)

    def _center(self, parent):
        self.update_idletasks()
        w = max(self.winfo_width(), 400)
        h = max(self.winfo_height(), 360)
        self.geometry(f"{w}x{h}")
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
