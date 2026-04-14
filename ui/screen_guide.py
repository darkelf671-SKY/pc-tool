"""사용법 안내 화면 (목업 동일)"""

import tkinter as tk
from ui.design_system import COLORS, FONTS, SPACING, BG_SURFACE
import config


class ScreenGuide(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["white"])
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

        # ── 3단계 사용법 (목업: .step-flow — 가로 3장 카드)
        step_area = tk.Frame(inner, bg=COLORS["white"])
        step_area.pack(fill="x", padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]))

        steps = [
            ("1", "증상 선택", "홈 화면에서 증상과\n가장 비슷한 카테고리를\n선택하세요"),
            ("2", "확인", "도구가 어떤 작업을\n하는지 확인하고\n'실행하기'를 누르세요"),
            ("3", "완료", "자동으로 문제를\n해결합니다. 실패하면\n원격 지원을 요청하세요"),
        ]

        # 가로 배치 (목업: flex, gap:8px)
        for i, (num, title, desc) in enumerate(steps):
            card = tk.Frame(
                step_area, bg=COLORS["white"],
                highlightbackground=COLORS["gray_200"], highlightthickness=1,
            )
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if i == 0 else 4, 0 if i == 2 else 4))

            card_inner = tk.Frame(card, bg=COLORS["white"], padx=12, pady=16)
            card_inner.pack(fill="both", expand=True)

            # 번호 원 (목업: .step-num, 28x28, brand bg, white number)
            num_frame = tk.Frame(card_inner, bg=COLORS["brand"],
                                 width=28, height=28)
            num_frame.pack()
            num_frame.pack_propagate(False)
            tk.Label(
                num_frame, text=num,
                font=("맑은 고딕", 11, "bold"), bg=COLORS["brand"],
                fg=COLORS["white"],
            ).pack(expand=True)

            # 제목 (목업: .step-title)
            tk.Label(
                card_inner, text=title,
                font=FONTS["body_bold"], bg=COLORS["white"],
                fg=COLORS["gray_800"],
            ).pack(pady=(8, 4))

            # 설명 (목업: .step-desc)
            tk.Label(
                card_inner, text=desc,
                font=FONTS["tag"], bg=COLORS["white"],
                fg=COLORS["gray_500"], justify="center",
            ).pack()

            # 화살표 (마지막 카드 제외, 목업: .step-arrow)
            if i < 2:
                arrow = tk.Label(
                    step_area, text="→",
                    font=("맑은 고딕", 16), bg=COLORS["white"],
                    fg=COLORS["gray_300"],
                )
                arrow.pack(side="left", padx=2)

        # ── FAQ (목업: .faq-item)
        faq_header = tk.Frame(inner, bg=COLORS["white"])
        faq_header.pack(fill="x", padx=SPACING["xl"],
                        pady=(SPACING["xl"], SPACING["md"]))
        tk.Label(
            faq_header, text="자주 묻는 질문",
            font=FONTS["subheading"], bg=COLORS["white"],
            fg=COLORS["gray_900"],
        ).pack(anchor="w")

        faq_area = tk.Frame(inner, bg=COLORS["white"])
        faq_area.pack(fill="x")

        faqs = [
            ("관리자 권한 팝업이 나와요",
             "정상입니다. 시스템 설정을 변경하려면 관리자 권한이 필요합니다. '예'를 눌러주세요."),
            ("재부팅하라고 하면 꼭 해야 하나요?",
             "네, 일부 도구는 재부팅 후에 완전히 적용됩니다. 작업 저장 후 재부팅해주세요."),
            ("실행했는데도 안 돼요",
             "다른 해결 방법을 시도하거나, '원격 지원'을 요청하세요."),
            ("프로그램이 자동으로 업데이트돼요",
             "새 버전이 나오면 실행 시 자동으로 업데이트됩니다. 별도 조작은 필요 없습니다."),
            ("이 프로그램은 안전한가요?",
             "서울재활병원 전산팀에서 직접 만든 내부 도구입니다. 의문사항은 전산팀에 문의하세요."),
        ]

        for q, a in faqs:
            self._create_faq_item(faq_area, q, a)

        # ── 푸터
        footer = tk.Frame(inner, bg=COLORS["gray_50"])
        footer.pack(fill="x", pady=(SPACING["xl"], 0))
        tk.Frame(footer, bg=COLORS["gray_200"], height=1).pack(fill="x")
        tk.Label(
            footer,
            text=f"{config.APP_NAME} v{config.APP_VERSION}\n{config.AUTHOR}",
            font=FONTS["tag"], bg=COLORS["gray_50"],
            fg=COLORS["gray_400"], justify="center",
        ).pack(pady=SPACING["lg"])

    def _create_faq_item(self, parent, question: str, answer: str):
        """목업: .faq-item — Q 배지 + 질문 + 답변"""
        item = tk.Frame(parent, bg=COLORS["white"])
        item.pack(fill="x")

        inner = tk.Frame(item, bg=COLORS["white"], padx=SPACING["xl"], pady=14)
        inner.pack(fill="x")

        # 질문 행 (목업: .faq-q — Q 배지 + 텍스트)
        q_row = tk.Frame(inner, bg=COLORS["white"])
        q_row.pack(fill="x")

        # Q 배지 (목업: 20x20, brand bg, white "Q")
        q_badge = tk.Frame(q_row, bg=COLORS["brand"], width=20, height=20)
        q_badge.pack(side="left", anchor="n", pady=(2, 0))
        q_badge.pack_propagate(False)
        tk.Label(
            q_badge, text="Q",
            font=("맑은 고딕", 8, "bold"), bg=COLORS["brand"],
            fg=COLORS["white"],
        ).pack(expand=True)

        tk.Label(
            q_row, text=question,
            font=FONTS["body_bold"], bg=COLORS["white"],
            fg=COLORS["gray_800"], anchor="w",
            wraplength=380, justify="left",
        ).pack(side="left", padx=(6, 0))

        # 답변 (목업: .faq-a, padding-left:26px)
        tk.Label(
            inner, text=answer,
            font=FONTS["small"], bg=COLORS["white"],
            fg=COLORS["gray_600"], anchor="w",
            wraplength=380, justify="left",
        ).pack(fill="x", padx=(26, 0), pady=(6, 0))

        # 하단 구분선
        tk.Frame(item, bg=COLORS["gray_100"], height=1).pack(
            fill="x", padx=SPACING["xl"],
        )
