"""⑩ 시스템 파일 검사 (SFC + DISM)"""

from tools.base import BaseTool


class SfcScanTool(BaseTool):
    tool_id = "sfc_scan"
    name = "시스템 파일 검사"
    requires_admin = True
    requires_reboot = True

    def get_steps(self):
        return ["DISM 이미지 복구", "SFC 시스템 파일 검사"]

    def run(self, log):
        # Step 0: DISM (최대 10분)
        log("DISM 이미지 복구 시작 (5~15분 소요)...", -1)
        code, output = self._run_cmd(
            "DISM /Online /Cleanup-Image /RestoreHealth",
            log, timeout=600,
        )
        if code == 0:
            log("DISM 이미지 복구 완료", 0)
        else:
            log("DISM 복구 실패 (SFC로 계속 진행)", 0)

        # Step 1: SFC (최대 10분)
        log("SFC 시스템 파일 검사 시작 (5~15분 소요)...", -1)
        code, output = self._run_cmd(
            "sfc /scannow", log, timeout=600,
        )
        if code == 0:
            log("시스템 파일 검사 완료. 재부팅을 권장합니다.", 1)
        else:
            log("SFC 검사 완료 (일부 파일 복구 불가)", 1)

        return code == 0
