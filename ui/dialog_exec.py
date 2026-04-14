"""실행 중 다이얼로그 — 진행률 + 다크 터미널 로그 (목업 동일)"""

import tkinter as tk
import threading
import time
from ui.design_system import COLORS, FONTS, SPACING
from tools.base import BaseTool


class ExecDialog(tk.Toplevel):
    def __init__(self, parent, symptom: dict, tool: BaseTool, on_complete):
        super().__init__(parent)
        self.title("실행 중...")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.configure(bg=COLORS["white"])

        self._symptom = symptom
        self._tool = tool
        self._on_complete = on_complete
        self._steps = tool.get_steps()
        self._step_labels: list[tk.Label] = []
        self._step_icons: list[tk.Label] = []

        self._build()
        self._center(parent)
        self._start()

    def _build(self):
        f = tk.Frame(self, bg=COLORS["white"], padx=24, pady=24)
        f.pack(fill="both", expand=True)

        # 중앙 아이콘 (목업: .exec-icon, 56px)
        tk.Label(
            f, text="⏳", font=("Segoe UI Emoji", 40),
            bg=COLORS["white"],
        ).pack()

        # 제목 (목업: .exec-title, 중앙)
        tk.Label(
            f, text=f"{self._symptom.get('title', '')} 실행 중...",
            font=(FONTS["heading"][0], 15, "bold"), bg=COLORS["white"],
            fg=COLORS["gray_900"],
        ).pack(pady=(12, 6))

        # 설명 (목업: .exec-desc, 중앙)
        tk.Label(
            f, text="잠시만 기다려주세요. 자동으로 진행됩니다.",
            font=FONTS["body"], bg=COLORS["white"],
            fg=COLORS["gray_500"],
        ).pack(pady=(0, SPACING["xl"]))

        # 진행률 바 (목업: .exec-progress, 4px)
        self._progress_frame = tk.Frame(
            f, bg=COLORS["gray_200"], height=4,
        )
        self._progress_frame.pack(fill="x")
        self._progress_frame.pack_propagate(False)
        self._progress_bar = tk.Frame(
            self._progress_frame, bg=COLORS["brand"], height=4,
        )
        self._progress_bar.place(x=0, y=0, relheight=1, relwidth=0)

        # 단계 표시 (목업: .exec-steps — gray-50, border)
        if self._steps:
            steps_box = tk.Frame(
                f, bg=COLORS["gray_50"],
                highlightbackground=COLORS["gray_200"], highlightthickness=1,
            )
            steps_box.pack(fill="x", pady=(SPACING["xl"], 0))

            steps_inner = tk.Frame(steps_box, bg=COLORS["gray_50"],
                                    padx=20, pady=16)
            steps_inner.pack(fill="x")

            for i, step_text in enumerate(self._steps):
                row = tk.Frame(steps_inner, bg=COLORS["gray_50"])
                row.pack(fill="x", pady=4)

                # 상태 아이콘 (목업: .si — ○/⏳/✅)
                icon_lbl = tk.Label(
                    row, text="○", font=("Segoe UI Emoji", 12),
                    bg=COLORS["gray_50"], fg=COLORS["gray_400"],
                    width=3,
                )
                icon_lbl.pack(side="left")

                step_lbl = tk.Label(
                    row, text=step_text,
                    font=FONTS["body"], bg=COLORS["gray_50"],
                    fg=COLORS["gray_400"], anchor="w",
                    wraplength=350, justify="left",
                )
                step_lbl.pack(side="left", padx=(6, 0))

                self._step_icons.append(icon_lbl)
                self._step_labels.append(step_lbl)

                # 구분선 (마지막 제외, 목업: border-bottom:1px gray-100)
                if i < len(self._steps) - 1:
                    tk.Frame(steps_inner, bg=COLORS["gray_100"],
                             height=1).pack(fill="x", pady=(4, 0))

        # 로그 영역 (목업: .exec-log — dark terminal)
        tk.Label(
            f, text="", bg=COLORS["white"],
        ).pack(pady=(SPACING["sm"], 0))

        self._log_text = tk.Text(
            f, height=5, width=52,
            font=FONTS["mono"],
            bg=COLORS["terminal_bg"],
            fg=COLORS["terminal_text"],
            state="disabled", wrap="word",
            borderwidth=0, relief="flat",
            insertbackground=COLORS["terminal_text"],
            selectbackground="#2D2D4A",
            padx=16, pady=14,
        )
        self._log_text.pack(fill="x")

        # 로그 태그 설정
        self._log_text.tag_configure(
            "time", foreground=COLORS["terminal_time"],
        )
        self._log_text.tag_configure(
            "ok", foreground="#4ADE80",
        )

    def _start(self):
        self._start_time = time.time()
        # 첫 번째 단계를 active로
        if self._step_labels:
            self._step_icons[0].configure(text="⏳", fg=COLORS["gray_800"])
            self._step_labels[0].configure(
                fg=COLORS["gray_800"],
                font=FONTS["body_bold"],
            )
        thread = threading.Thread(target=self._run_tool, daemon=True)
        thread.start()

    def _run_tool(self):
        try:
            success = self._tool.run(log=self._on_log)
        except Exception as e:
            self._on_log(f"오류 발생: {e}", -1)
            success = False
        duration = time.time() - self._start_time
        self.after(100, self._finish, success, duration)

    def _on_log(self, message: str, step_index: int = -1):
        self.after(0, self._update_ui, message, step_index)

    def _update_ui(self, message: str, step_index: int):
        # 단계 완료 표시 (목업: .exec-step.done)
        if 0 <= step_index < len(self._step_labels):
            self._step_icons[step_index].configure(
                text="✅", fg=COLORS["brand_dark"],
            )
            self._step_labels[step_index].configure(
                fg=COLORS["brand_dark"],
                font=FONTS["body"],
            )
            # 다음 단계 active (목업: .exec-step.active)
            next_idx = step_index + 1
            if next_idx < len(self._step_labels):
                self._step_icons[next_idx].configure(
                    text="⏳", fg=COLORS["gray_800"],
                )
                self._step_labels[next_idx].configure(
                    fg=COLORS["gray_800"],
                    font=FONTS["body_bold"],
                )
            # 진행률
            progress = (step_index + 1) / max(len(self._steps), 1)
            self._progress_bar.place(relwidth=progress)

        # 로그 추가 (목업: dark terminal, colored tags)
        ts = time.strftime("%H:%M:%S")
        self._log_text.configure(state="normal")
        self._log_text.insert("end", "[", "time")
        self._log_text.insert("end", ts, "time")
        self._log_text.insert("end", "] ", "time")

        if step_index >= 0:
            self._log_text.insert("end", f"{message}\n", "ok")
        else:
            self._log_text.insert("end", f"{message}\n")

        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _finish(self, success: bool, duration: float):
        self._progress_bar.place(relwidth=1.0)
        self.after(500, lambda: self._close_and_callback(success, duration))

    def _close_and_callback(self, success, duration):
        self.grab_release()
        self.destroy()
        self._on_complete(self._symptom, success, duration)

    def _center(self, parent):
        self.update_idletasks()
        w = max(self.winfo_width(), 460)
        h = max(self.winfo_height(), 480)
        self.geometry(f"{w}x{h}")
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
