"""결과 다이얼로그 — 성공/실패 + 후속 안내 (목업 동일)"""

import tkinter as tk
import webbrowser
from ui.design_system import COLORS, FONTS, SPACING
import config


class ResultDialog(tk.Toplevel):
    def __init__(self, parent, symptom: dict, success: bool,
                 duration: float, on_close=None):
        super().__init__(parent)
        self.title("실행 결과")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=COLORS["white"])

        self._symptom = symptom
        self._success = success
        self._duration = duration
        self._on_close = on_close
        self._build()
        self._center(parent)

    def _build(self):
        f = tk.Frame(self, bg=COLORS["white"], padx=28, pady=40)
        f.pack(fill="both", expand=True)

        if self._success:
            self._build_success(f)
        else:
            self._build_failure(f)

    def _build_success(self, f):
        """목업: .result-container (성공)"""
        # 아이콘 (목업: .result-icon, 64px)
        tk.Label(
            f, text="✅", font=("Segoe UI Emoji", 48),
            bg=COLORS["white"],
        ).pack()

        # 제목 (목업: .result-title, brand-dark)
        tk.Label(
            f, text="해결 완료!",
            font=(FONTS["heading"][0], 18, "bold"), bg=COLORS["white"],
            fg=COLORS["brand_dark"],
        ).pack(pady=(16, 8))

        # 설명 (목업: .result-desc)
        desc = f"{self._symptom.get('title', '')}이(가) 성공적으로 완료되었습니다."
        tk.Label(
            f, text=desc,
            font=FONTS["body"], bg=COLORS["white"],
            fg=COLORS["gray_500"], wraplength=360,
        ).pack(pady=(0, SPACING["xl"]))

        # 재부팅 안내 (필요시)
        from tools.registry import get_tool
        tool = get_tool(self._symptom.get("tool_id", ""))
        needs_reboot = tool and tool.requires_reboot

        # 팁 박스 (목업: .result-tip — brand-bg, 좌측 정렬)
        tip_text = self._symptom.get("success_tip", "")
        if needs_reboot:
            tip_text = "다음 단계: 재부팅 후에 완전히 적용됩니다. 작업을 저장하고 재부팅해주세요."
        if not tip_text:
            tip_text = "다음 단계: 문제가 해결되었는지 확인해보세요. 아직 증상이 있으면 다른 방법을 시도해보세요."

        tip_frame = tk.Frame(f, bg=COLORS["brand_bg"], padx=20, pady=16)
        tip_frame.pack(fill="x", pady=(0, SPACING["xl"]))
        tk.Label(
            tip_frame, text=f"💡 {tip_text}",
            font=FONTS["body"], bg=COLORS["brand_bg"],
            fg=COLORS["gray_700"], wraplength=340,
            justify="left", anchor="w",
        ).pack(fill="x")

        # 버튼 (목업: .exec-btns — pill 버튼)
        btn_frame = tk.Frame(f, bg=COLORS["white"])
        btn_frame.pack()

        # "다른 방법 시도" (목업: .btn-secondary)
        sec_btn = tk.Label(
            btn_frame, text="  다른 방법 시도  ",
            font=FONTS["body"], bg=COLORS["white"],
            fg=COLORS["gray_700"], padx=24, pady=10, cursor="hand2",
            highlightbackground=COLORS["gray_300"], highlightthickness=1,
        )
        sec_btn.pack(side="left", padx=(0, 10))
        sec_btn.bind("<Button-1>", lambda e: self._close())

        def _sec_enter(e):
            sec_btn.configure(
                highlightbackground=COLORS["brand"],
                fg=COLORS["brand"],
            )
        def _sec_leave(e):
            sec_btn.configure(
                highlightbackground=COLORS["gray_300"],
                fg=COLORS["gray_700"],
            )
        sec_btn.bind("<Enter>", _sec_enter)
        sec_btn.bind("<Leave>", _sec_leave)

        # "홈으로 돌아가기" (목업: .btn-primary)
        pri_btn = tk.Label(
            btn_frame, text="  홈으로 돌아가기  ",
            font=FONTS["body_bold"], bg=COLORS["brand"],
            fg=COLORS["white"], padx=24, pady=10, cursor="hand2",
        )
        pri_btn.pack(side="left")
        pri_btn.bind("<Button-1>", lambda e: self._close())

        def _pri_enter(e):
            pri_btn.configure(bg=COLORS["brand_dark"])
        def _pri_leave(e):
            pri_btn.configure(bg=COLORS["brand"])
        pri_btn.bind("<Enter>", _pri_enter)
        pri_btn.bind("<Leave>", _pri_leave)

    def _build_failure(self, f):
        """목업: 실패 결과"""
        # 아이콘
        tk.Label(
            f, text="❌", font=("Segoe UI Emoji", 48),
            bg=COLORS["white"],
        ).pack()

        # 제목
        tk.Label(
            f, text="해결되지 않았어요",
            font=(FONTS["heading"][0], 18, "bold"), bg=COLORS["white"],
            fg=COLORS["danger"],
        ).pack(pady=(16, 8))

        # 설명
        tk.Label(
            f, text="자동 해결에 실패했습니다.\n다른 방법을 시도하거나 원격 지원을 요청하세요.",
            font=FONTS["body"], bg=COLORS["white"],
            fg=COLORS["gray_500"], wraplength=360, justify="center",
        ).pack(pady=(0, SPACING["xl"]))

        # 실패 팁
        fail_tip = self._symptom.get("fail_tip", "")
        if fail_tip:
            tip_frame = tk.Frame(
                f, bg=COLORS["danger_light"], padx=20, pady=16,
            )
            tip_frame.pack(fill="x", pady=(0, SPACING["xl"]))
            tk.Label(
                tip_frame, text=fail_tip,
                font=FONTS["body"], bg=COLORS["danger_light"],
                fg=COLORS["gray_700"], wraplength=340,
                justify="left", anchor="w",
            ).pack(fill="x")

        # 버튼
        btn_frame = tk.Frame(f, bg=COLORS["white"])
        btn_frame.pack()

        # 확인 (secondary)
        close_btn = tk.Label(
            btn_frame, text="  확인  ",
            font=FONTS["body"], bg=COLORS["white"],
            fg=COLORS["gray_700"], padx=24, pady=10, cursor="hand2",
            highlightbackground=COLORS["gray_300"], highlightthickness=1,
        )
        close_btn.pack(side="left", padx=(0, 10))
        close_btn.bind("<Button-1>", lambda e: self._close())

        # 원격 지원 (danger)
        remote_btn = tk.Label(
            btn_frame, text="  📞 원격 지원  ",
            font=FONTS["body_bold"], bg=COLORS["danger"],
            fg=COLORS["white"], padx=24, pady=10, cursor="hand2",
        )
        remote_btn.pack(side="left")
        remote_btn.bind("<Button-1>", lambda e: self._open_remote())

        def _rem_enter(e):
            remote_btn.configure(bg="#C20111")
        def _rem_leave(e):
            remote_btn.configure(bg=COLORS["danger"])
        remote_btn.bind("<Enter>", _rem_enter)
        remote_btn.bind("<Leave>", _rem_leave)

    def _open_remote(self):
        webbrowser.open(config.REMOTE_SUPPORT_URL)

    def _close(self):
        self.grab_release()
        self.destroy()
        if self._on_close:
            self._on_close()

    def _center(self, parent):
        self.update_idletasks()
        w = max(self.winfo_width(), 420)
        h = max(self.winfo_height(), 400)
        self.geometry(f"{w}x{h}")
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
